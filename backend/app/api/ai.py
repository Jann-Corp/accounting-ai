from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import base64
import os
import uuid
import asyncio
import json
from datetime import datetime

import httpx

from app.database import get_db
from app.models.record import Record, RecordStatus, RecordType
from app.models.category import Category, CategoryType
from app.models.ai_recognition_job import AIRecognitionJob, RecognitionStatus
from app.schemas.ai_recognition_job import (
    AIRecognitionJobResponse,
    AIRecognitionJobDetailResponse,
    TaskStatusResponse,
)
from app.services.ai_service import ai_service
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI识别"])


def _run_recognition_sync(job_id: int, file_path: str, image_base64: str,
                          api_key: str | None, api_base: str | None,
                          model: str | None, prompt: str | None):
    """Synchronous recognition runner (runs in FastAPI BackgroundTasks thread)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(str(settings.DATABASE_URL))
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Update status to processing
        job = db.query(AIRecognitionJob).filter(AIRecognitionJob.id == job_id).first()
        if not job:
            return
        job.status = RecognitionStatus.PROCESSING
        db.commit()

        # Call AI service (blocking, up to 120s)
        ai_results = asyncio.run(_call_ai_service(image_base64, api_key, api_base, model, prompt))

        if not isinstance(ai_results, list):
            ai_results = [ai_results] if ai_results else []

        all_records = []
        for ai_result in ai_results:
            if not ai_result:
                continue

            category_id = None
            if ai_result.get("category_guess"):
                category = db.query(Category).filter(
                    Category.user_id == job.user_id,
                    Category.category_type == CategoryType.EXPENSE,
                    Category.name == ai_result["category_guess"]
                ).first()
                if category:
                    category_id = category.id

            amount = ai_result.get("amount") or 0
            record_type = RecordType.INCOME if amount < 0 else RecordType.EXPENSE

            all_records.append({
                "amount": abs(amount) if amount != 0 else 0,
                "record_type": record_type.value if hasattr(record_type, 'value') else str(record_type),
                "merchant_name": ai_result.get("merchant_name"),
                "date": ai_result.get("date"),
                "category_guess": ai_result.get("category_guess"),
                "category_id": category_id,
                "confidence": ai_result.get("confidence", 0.0),
                "raw_response": ai_result.get("raw_response"),
            })

        overall_confidence = (
            sum(r["confidence"] for r in all_records) / len(all_records)
            if all_records else 0.0
        )
        auto_confirm = overall_confidence >= settings.AI_CONFIDENCE_THRESHOLD

        # Store result JSON (immutable log)
        first = all_records[0] if all_records else {}
        result_payload = {
            "amount": first.get("amount"),
            "merchant_name": first.get("merchant_name"),
            "date": first.get("date"),
            "category_guess": first.get("category_guess"),
            "category_id": first.get("category_id"),
            "confidence": overall_confidence,
            "original_image_url": file_path,
            "raw_response": first.get("raw_response"),
            "records": all_records,
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


async def _call_ai_service(image_base64: str, api_key: str | None, api_base: str | None,
                           model: str | None, prompt: str | None) -> list:
    """Make the actual AI API call with 120s timeout."""
    if not api_key:
        return [{
            "amount": 128.50,
            "merchant_name": "测试商家",
            "date": "2024-01-15",
            "category_guess": "餐饮",
            "confidence": 0.85,
            "raw_response": "Mock response - API key not configured"
        }]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model or "qwen-vl-plus",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt or settings.AI_RECOGNITION_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                }
            ]
        }],
        "max_tokens": 500,
        "temperature": 0.1
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{api_base or settings.QWEN_API_BASE}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        try:
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                records = [data]
            else:
                records = []

            return [
                {
                    "amount": r.get("amount"),
                    "merchant_name": r.get("merchant_name"),
                    "date": r.get("date"),
                    "category_guess": r.get("category_guess"),
                    "confidence": r.get("confidence", 0.5),
                    "raw_response": json.dumps(r, ensure_ascii=False)
                }
                for r in records
                if isinstance(r, dict)
            ] if records else [{
                "amount": None,
                "merchant_name": None,
                "date": None,
                "category_guess": None,
                "confidence": 0.0,
                "raw_response": content,
            }]
        except json.JSONDecodeError:
            return [{
                "amount": None,
                "merchant_name": None,
                "date": None,
                "category_guess": None,
                "confidence": 0.0,
                "raw_response": content,
            }]


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
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
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

    # Create DB job record (immutable log)
    job = AIRecognitionJob(
        user_id=current_user.id,
        original_image_url=file_path,
        status=RecognitionStatus.PENDING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Run recognition in background (non-blocking, up to 120s)
    background_tasks.add_task(
        _run_recognition_sync,
        job.id,
        file_path,
        image_base64,
        settings.QWEN_API_KEY,
        settings.QWEN_API_BASE,
        settings.QWEN_MODEL,
        settings.AI_RECOGNITION_PROMPT,
    )

    return {
        "task_id": str(job.id),
        "status": "pending",
        "message": "图片已接收，AI 正在识别中，预计需要 10-60 秒",
    }


@router.get("/recognize/{job_id}")
async def get_recognition_result(job_id: int, db: Session = Depends(get_db)):
    """查询识别任务状态和结果（job_id 即 task_id）。"""
    job = db.query(AIRecognitionJob).filter(AIRecognitionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Task not found")

    if job.status == RecognitionStatus.PENDING:
        return TaskStatusResponse(
            task_id=str(job.id),
            status="pending",
            message="排队中..."
        )

    if job.status == RecognitionStatus.PROCESSING:
        return TaskStatusResponse(
            task_id=str(job.id),
            status="pending",
            message="AI 正在识别中，请稍候..."
        )

    if job.status == RecognitionStatus.FAILED:
        return TaskStatusResponse(
            task_id=str(job.id),
            status="error",
            message=job.error_message or "识别失败"
        )

    # DONE — return full result
    result_data = json.loads(job.result_json) if job.result_json else {}
    records = result_data.get("records", [])

    return {
        "task_id": str(job.id),
        "status": "done",
        "result": {
            "amount": result_data.get("amount"),
            "merchant_name": result_data.get("merchant_name"),
            "date": result_data.get("date"),
            "category_guess": result_data.get("category_guess"),
            "category_id": result_data.get("category_id"),
            "confidence": result_data.get("confidence"),
            "original_image_url": result_data.get("original_image_url"),
            "raw_response": result_data.get("raw_response"),
            "records": records,
        }
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


@router.get("/jobs/{job_id}", response_model=AIRecognitionJobDetailResponse)
async def get_recognition_job_detail(
    job_id: int,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """获取识别记录详情（含识别结果 JSON）。"""
    current_user = _get_current_user(x_api_key, authorization, db)
    job = db.query(AIRecognitionJob).filter(
        AIRecognitionJob.id == job_id,
        AIRecognitionJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Not found")

    result_data = json.loads(job.result_json) if job.result_json else {}
    records = result_data.get("records", [])

    return AIRecognitionJobDetailResponse(
        id=job.id,
        user_id=job.user_id,
        original_image_url=job.original_image_url,
        status=job.status,
        result_json=job.result_json,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
        records=records,
    )
