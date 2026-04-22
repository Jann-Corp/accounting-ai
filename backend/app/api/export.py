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
from app.api.deps import get_current_user_or_api_key
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
    import sys
    print(f"DEBUG export endpoint: x_api_key={x_api_key!r}, format={format}", file=sys.stdout, flush=True)
    
    # Determine which auth to use
    auth_token = None
    if x_api_key:
        auth_token = x_api_key
    elif authorization and authorization.startswith("Bearer "):
        auth_token = authorization[7:]
    
    if not auth_token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    current_user = get_current_user_or_api_key(x_api_key=auth_token, db=db)

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
