from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session
from typing import Optional
import base64
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.models.record import Record, RecordStatus, RecordType
from app.models.category import Category, CategoryType
from app.schemas.record import AIRecognizeResponse
from app.services.ai_service import ai_service
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI识别"])


@router.post("/recognize", response_model=AIRecognizeResponse)
async def recognize_receipt(
    file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    # Auth: prefer X-API-Key, fallback to Bearer JWT
    if x_api_key:
        from app.api.deps import get_current_user_or_api_key
        current_user = get_current_user_or_api_key(x_api_key=x_api_key, db=db)
    elif authorization and authorization.startswith("Bearer "):
        from app.core.security import decode_token
        token = authorization[7:]
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        current_user = user
    else:
        raise HTTPException(status_code=401, detail="Missing authentication")
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
        raise HTTPException(status_code=400, detail="只支持 JPEG、PNG、WebP 格式的图片")
    
    # Read and encode image
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过10MB")
    
    image_base64 = base64.b64encode(contents).decode("utf-8")
    
    # Save file locally
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Call AI service
    ai_result = await ai_service.recognize_receipt(image_base64)
    
    # Find matching category
    category_id = None
    if ai_result.get("category_guess"):
        category = db.query(Category).filter(
            Category.user_id == current_user.id,
            Category.category_type == CategoryType.EXPENSE,
            Category.name == ai_result["category_guess"]
        ).first()
        if category:
            category_id = category.id
    
    # Determine status based on confidence
    confidence = ai_result.get("confidence", 0.0)
    auto_confirm = confidence >= settings.AI_CONFIDENCE_THRESHOLD
    
    # Create record
    record = Record(
        user_id=current_user.id,
        amount=ai_result.get("amount") or 0,
        record_type=RecordType.EXPENSE,
        date=datetime.utcnow(),
        original_image_url=file_path,
        ai_confidence=confidence,
        status=RecordStatus.CONFIRMED if auto_confirm else RecordStatus.PENDING,
        note=ai_result.get("merchant_name") or "AI识别",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # Return AI response
    return AIRecognizeResponse(
        amount=ai_result.get("amount"),
        merchant_name=ai_result.get("merchant_name"),
        date=ai_result.get("date"),
        category_guess=ai_result.get("category_guess"),
        category_id=category_id,
        confidence=confidence,
        original_image_url=file_path,
        raw_response=ai_result.get("raw_response"),
    )
