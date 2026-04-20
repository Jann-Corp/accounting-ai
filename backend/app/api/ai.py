from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, BackgroundTasks
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

router = APIRouter(prefix="/ai", tags=["AI识别"])


def _run_recognition_sync(job_id: int, file_path: str, image_base64: str):
    """Background task: call AI service and persist result to DB job record."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
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
    file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """上传小票图片，立即返回 job_id，后台异步识别。"""
    current_user = _get_current_user(x_api_key, authorization, db)

    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
        raise HTTPException(status_code=400, detail="只支持 JPEG、PNG、WebP 格式的图片")

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过10MB")

    image_base64 = base64.b64encode(contents).decode("utf-8")

    # Save image
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
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
