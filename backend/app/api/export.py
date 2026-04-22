from fastapi import APIRouter, Depends, Query, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.record import Record, RecordType, RecordStatus
from app.models.wallet import Wallet
from app.models.category import Category
from app.models.apikey import ApiKey
from app.models.user import User

router = APIRouter(prefix="/records", tags=["导出"])


@router.get("/export")
def export_records(
    format: str = Query(default="csv", regex="^(csv|json)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    record_type: Optional[RecordType] = None,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    """
    Export records as CSV or JSON.
    Supports both Bearer token (Authorization header) and X-API-Key header authentication.
    """
    # Try Bearer token first, then API key
    from app.core.security import decode_token
    import hashlib
    current_user = None
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = decode_token(token)
        if payload:
            user_id = int(payload.get("sub"))
            current_user = db.query(User).filter(User.id == user_id).first()
    elif x_api_key:
        key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
        api_key = db.query(ApiKey).filter(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,
        ).first()
        if api_key:
            # Check expiry
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired",
                )
            # Update last_used_at
            api_key.last_used_at = datetime.utcnow()
            db.commit()
            current_user = api_key.user
    
    if current_user is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    if not current_user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    query = db.query(Record).filter(Record.user_id == current_user.id)

    if start_date:
        query = query.filter(Record.date >= start_date)
    if end_date:
        query = query.filter(Record.date <= end_date)
    if record_type:
        query = query.filter(Record.record_type == record_type)

    records = query.order_by(Record.date.desc()).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "ID", "日期", "类型", "金额", "账户", "分类", "备注",
            "AI置信度", "状态", "创建时间"
        ])

        for r in records:
            writer.writerow([
                r.id,
                r.date.strftime("%Y-%m-%d %H:%M:%S"),
                "支出" if r.record_type == RecordType.EXPENSE else "收入",
                r.amount,
                r.wallet.name if r.wallet else "",
                r.category.name if r.category else "",
                r.note or "",
                r.ai_confidence or "",
                r.status.value,
                r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])

        output.seek(0)
        filename = f"records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    else:
        data = []
        for r in records:
            data.append({
                "id": r.id,
                "date": r.date.isoformat(),
                "type": r.record_type.value,
                "amount": r.amount,
                "wallet": r.wallet.name if r.wallet else None,
                "category": r.category.name if r.category else None,
                "note": r.note,
                "ai_confidence": r.ai_confidence,
                "status": r.status.value,
                "created_at": r.created_at.isoformat(),
            })

        import json
        filename = f"records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        return StreamingResponse(
            iter([json.dumps(data, ensure_ascii=False, indent=2)]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
