from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Optional
import base64
import os
import uuid
import json
from datetime import datetime
from app.database import get_db
from app.models.ai_recognition_job import AIRecognitionJob, RecognitionStatus
from app.schemas.ai_recognition_job import (
    AIRecognitionJobResponse,
    TaskStatusResponse,
)
from app.services.ai_service import ai_service
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI 识别"])


def _run_recognition_sync(job_id: int, file_path: str, image_base64: str):
    """Background task: call AI service and persist result to DB job record.
    
    Auto-save records based on confidence threshold:
    - confidence >= threshold: create Record with status=CONFIRMED
    - confidence < threshold: create Record with status=PENDING (user review needed)
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.record import Record, RecordStatus
    from app.models.category import Category
    from datetime import datetime
    
    engine = create_engine(str(settings.DATABASE_URL))
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        job = db.query(AIRecognitionJob).filter(AIRecognitionJob.id == job_id).first()
        if not job:
            return
        job.status = RecognitionStatus.PROCESSING
        db.commit()

        # Call AI service (up to 120s timeout defined in ai_service)
        import asyncio
        ai_results = asyncio.run(ai_service.recognize_receipt(image_base64))

        # Normalize: ensure list
        if not isinstance(ai_results, list):
            ai_results = [ai_results] if ai_results else []

        # Build result payload (immutable log)
        result_payload = {
            "records": [
                {
                    "amount": r.get("amount"),
                    "record_type": r.get("record_type", "expense"),
                    "merchant_name": r.get("merchant_name"),
                    "date": r.get("date"),
                    "category_guess": r.get("category_guess"),
                    "category_id": r.get("category_id"),
                    "confidence": r.get("confidence", 0.0),
                    "raw_response": r.get("raw_response"),
                }
                for r in ai_results
            ],
            "original_image_url": file_path,
        }

        # Auto-create Record entries based on confidence
        created_records = []
        
        # Get user's default wallet (or first wallet)
        user_wallets = db.query(Wallet).filter(Wallet.user_id == job.user_id).all()
        default_wallet = None
        if user_wallets:
            # Try to find user's default wallet first
            user_obj = db.query(User).filter(User.id == job.user_id).first()
            if user_obj and user_obj.default_wallet_id:
                default_wallet = db.query(Wallet).filter(
                    Wallet.id == user_obj.default_wallet_id,
                    Wallet.user_id == job.user_id
                ).first()
            # Fallback to first wallet
            if not default_wallet:
                default_wallet = user_wallets[0]
        
        for r in ai_results:
            if not isinstance(r, dict):
                continue
            
            confidence = r.get("confidence", 0.0)
            amount = r.get("amount")
            if amount is None:
                continue  # Skip invalid records
            
            # Determine status based on confidence
            if confidence >= settings.AI_CONFIDENCE_THRESHOLD:
                status = RecordStatus.CONFIRMED
            else:
                status = RecordStatus.PENDING
            
            # Parse date
            date_str = r.get("date")
            if date_str:
                try:
                    # Try full datetime first
                    record_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    try:
                        # Try date only
                        record_date = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        record_date = datetime.now()
            else:
                record_date = datetime.now()
            
            # Find category by guess
            category_id = None
            category_guess = r.get("category_guess")
            if category_guess:
                cat = db.query(Category).filter(
                    Category.user_id == job.user_id,
                    Category.name == category_guess
                ).first()
                if cat:
                    category_id = cat.id
            
            # Create record with wallet_id
            record = Record(
                user_id=job.user_id,
                wallet_id=default_wallet.id if default_wallet else None,
                amount=amount,
                record_type=r.get("record_type", "expense"),
                note=r.get("merchant_name"),
                date=record_date,
                category_id=category_id,
                original_image_url=file_path,
                ai_confidence=confidence,
                is_ai_recognized=1,
                job_id=job.id,
                status=status,
            )
            db.add(record)
            created_records.append({
                "record_id": record.id,
                "status": status.value,
                "confidence": confidence,
            })
        
        db.commit()
        
        # Update job with results
        result_payload["created_records"] = created_records
        job.result_json = json.dumps(result_payload, ensure_ascii=False)
        job.status = RecognitionStatus.DONE
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        try:
            job = db.query(AIRecognitionJob).filter(AIRecognitionJob.id == job_id).first()
            if job:
                job.status = RecognitionStatus.FAILED
                job.error_message = str(e)[:1000]
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _get_current_user(x_api_key: Optional[str], authorization: Optional[str], db: Session) -> User:
    if x_api_key:
        from app.api.deps import get_current_user_or_api_key
        return get_current_user_or_api_key(x_api_key=x_api_key, db=db)
    if authorization and authorization.startswith("Bearer "):
        from app.core.security import decode_token
        token = authorization[7:]
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    raise HTTPException(status_code=401, detail="Missing authentication")


@router.post("/recognize")
async def recognize_receipt(
    background_tasks: BackgroundTasks,
    request: Request,
    file: Optional[UploadFile] = File(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """上传小票图片，立即返回 job_id，后台异步识别。
    
    支持两种格式：
    1. multipart/form-data（浏览器/Postman）：file 字段
    2. 原始图片数据（iOS Shortcuts）：request body 直接是图片二进制
    """
    current_user = _get_current_user(x_api_key, authorization, db)

    # 获取图片数据和内容类型
    contents = None
    content_type = None
    filename = None
    
    if file and file.filename:
        # multipart/form-data 格式
        contents = await file.read()
        content_type = file.content_type
        filename = file.filename
    else:
        # 原始图片数据（iOS Shortcuts）
        contents = await request.body()
        content_type = request.headers.get("content-type", "image/jpeg")
        filename = "upload.jpg"

    if not contents:
        raise HTTPException(status_code=400, detail="图片数据为空")
    
    # 验证图片格式
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if content_type and not any(t in content_type.lower() for t in allowed_types):
        raise HTTPException(status_code=400, detail="只支持 JPEG、PNG、WebP 格式的图片")

    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 10MB")

    image_base64 = base64.b64encode(contents).decode("utf-8")

    # Save image
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    ext = filename.split(".")[-1] if "." in filename else "jpg"
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{ext}"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    # Create immutable job record
    job = AIRecognitionJob(
        user_id=current_user.id,
        original_image_url=file_path,
        status=RecognitionStatus.PENDING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_run_recognition_sync, job.id, file_path, image_base64)

    return {
        "task_id": str(job.id),
        "status": "pending",
        "message": "图片已接收，AI 正在识别中，预计需要 10-60 秒",
    }


@router.get("/recognize/{job_id}")
async def get_recognition_result(job_id: int, db: Session = Depends(get_db)):
    """查询识别任务状态和结果。"""
    job = db.query(AIRecognitionJob).filter(AIRecognitionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Task not found")

    if job.status == RecognitionStatus.PENDING:
        return TaskStatusResponse(task_id=str(job.id), status="pending", message="排队中...")
    if job.status == RecognitionStatus.PROCESSING:
        return TaskStatusResponse(task_id=str(job.id), status="pending", message="AI 正在识别中，请稍候...")
    if job.status == RecognitionStatus.FAILED:
        return TaskStatusResponse(task_id=str(job.id), status="error", message=job.error_message or "识别失败")

    # DONE
    result_data = json.loads(job.result_json) if job.result_json else {}
    return {
        "task_id": str(job.id),
        "status": "done",
        "result": result_data,
    }


@router.get("/jobs", response_model=list[AIRecognitionJobResponse])
async def list_recognition_jobs(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """列出当前用户的所有识别记录（按时间倒序）。"""
    current_user = _get_current_user(x_api_key, authorization, db)
    jobs = db.query(AIRecognitionJob).filter(
        AIRecognitionJob.user_id == current_user.id
    ).order_by(AIRecognitionJob.created_at.desc()).all()
    return jobs


@router.get("/jobs/{job_id}")
async def get_recognition_job_detail(
    job_id: int,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """获取识别记录详情。"""
    current_user = _get_current_user(x_api_key, authorization, db)
    job = db.query(AIRecognitionJob).filter(
        AIRecognitionJob.id == job_id,
        AIRecognitionJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return job


@router.get("/records/pending")
async def list_pending_ai_records(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """列出所有待确认的 AI 识别记录（status=PENDING）。"""
    from app.models.record import Record, RecordStatus
    current_user = _get_current_user(x_api_key, authorization, db)
    
    records = db.query(Record).filter(
        Record.user_id == current_user.id,
        Record.status == RecordStatus.PENDING,
        Record.is_ai_recognized == 1,
    ).order_by(Record.created_at.desc()).all()
    
    return records


@router.post("/records/{record_id}/confirm")
async def confirm_ai_record(
    record_id: int,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """确认一条 AI 识别记录（PENDING → CONFIRMED）。"""
    from app.models.record import Record, RecordStatus
    current_user = _get_current_user(x_api_key, authorization, db)
    
    record = db.query(Record).filter(
        Record.id == record_id,
        Record.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    if record.status != RecordStatus.PENDING:
        raise HTTPException(status_code=400, detail="Record is not pending")
    
    record.status = RecordStatus.CONFIRMED
    db.commit()
    db.refresh(record)
    
    return {"status": "confirmed", "record_id": record_id}


@router.post("/records/{record_id}/reject")
async def reject_ai_record(
    record_id: int,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """拒绝一条 AI 识别记录（PENDING → REJECTED）。"""
    from app.models.record import Record, RecordStatus
    current_user = _get_current_user(x_api_key, authorization, db)
    
    record = db.query(Record).filter(
        Record.id == record_id,
        Record.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    if record.status != RecordStatus.PENDING:
        raise HTTPException(status_code=400, detail="Record is not pending")
    
    record.status = RecordStatus.REJECTED
    db.commit()
    db.refresh(record)
    
    return {"status": "rejected", "record_id": record_id}
