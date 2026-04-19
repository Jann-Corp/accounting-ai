from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.models.record import Record, RecordType, RecordStatus
from app.models.wallet import Wallet
from app.models.category import Category
from app.schemas.record import RecordCreate, RecordUpdate, RecordResponse, AIRecognizeResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/records", tags=["记录"])


def record_to_response(record: Record) -> RecordResponse:
    return RecordResponse(
        id=record.id,
        user_id=record.user_id,
        wallet_id=record.wallet_id,
        category_id=record.category_id,
        amount=record.amount,
        record_type=record.record_type,
        note=record.note,
        date=record.date,
        original_image_url=record.original_image_url,
        ai_confidence=record.ai_confidence,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
        wallet_name=record.wallet.name if record.wallet else None,
        category_name=record.category.name if record.category else None,
        category_icon=record.category.icon if record.category else None,
    )


@router.get("", response_model=List[RecordResponse])
def list_records(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    wallet_id: Optional[int] = None,
    category_id: Optional[int] = None,
    record_type: Optional[RecordType] = None,
    status: Optional[RecordStatus] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Record).options(
        joinedload(Record.wallet),
        joinedload(Record.category)
    ).filter(Record.user_id == current_user.id)

    if start_date:
        query = query.filter(Record.date >= start_date)
    if end_date:
        query = query.filter(Record.date <= end_date)
    if wallet_id:
        query = query.filter(Record.wallet_id == wallet_id)
    if category_id:
        query = query.filter(Record.category_id == category_id)
    if record_type:
        query = query.filter(Record.record_type == record_type)
    if status:
        query = query.filter(Record.status == status)

    records = query.order_by(Record.date.desc()).offset(offset).limit(limit).all()
    return [record_to_response(r) for r in records]


@router.post("", response_model=RecordResponse)
def create_record(
    record_data: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify wallet belongs to user
    if record_data.wallet_id:
        wallet = db.query(Wallet).filter(
            Wallet.id == record_data.wallet_id,
            Wallet.user_id == current_user.id
        ).first()
        if not wallet:
            raise HTTPException(status_code=404, detail="账户不存在")

    record = Record(
        user_id=current_user.id,
        wallet_id=record_data.wallet_id,
        category_id=record_data.category_id,
        amount=record_data.amount,
        record_type=record_data.record_type,
        note=record_data.note,
        date=record_data.date,
        status=RecordStatus.CONFIRMED,
    )

    # Update wallet balance
    if record_data.wallet_id:
        if record_data.record_type == RecordType.EXPENSE:
            wallet.balance -= record_data.amount
        else:
            wallet.balance += record_data.amount
        db.add(wallet)

    db.add(record)
    db.commit()
    db.refresh(record)

    return record_to_response(record)


@router.get("/pending", response_model=List[RecordResponse])
def list_pending_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = db.query(Record).options(
        joinedload(Record.wallet),
        joinedload(Record.category)
    ).filter(
        Record.user_id == current_user.id,
        Record.status == RecordStatus.PENDING
    ).order_by(Record.created_at.desc()).all()

    return [record_to_response(r) for r in records]


# NOTE: /{record_id} routes MUST be at the END of this file.
# FastAPI matches routes in definition order. Moving them after /pending, /
# ensures literal paths like /export are matched before the wildcard {record_id}.
# See: https://github.com/tiangolo/fastapi/issues/5530

@router.get("/{record_id}", response_model=RecordResponse)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(Record).options(
        joinedload(Record.wallet),
        joinedload(Record.category)
    ).filter(
        Record.id == record_id,
        Record.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    return record_to_response(record)


@router.put("/{record_id}", response_model=RecordResponse)
def update_record(
    record_id: int,
    record_data: RecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(Record).filter(
        Record.id == record_id,
        Record.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    old_amount = record.amount
    old_wallet_id = record.wallet_id

    if record_data.amount is not None:
        record.amount = record_data.amount
    if record_data.record_type is not None:
        record.record_type = record_data.record_type
    if record_data.date is not None:
        record.date = record_data.date
    if record_data.note is not None:
        record.note = record_data.note
    if record_data.wallet_id is not None:
        record.wallet_id = record_data.wallet_id
    if record_data.category_id is not None:
        record.category_id = record_data.category_id

    # If wallet changed or amount changed, update wallet balances
    if record.status == RecordStatus.CONFIRMED:
        # Reverse old transaction
        if old_wallet_id:
            old_wallet = db.query(Wallet).filter(Wallet.id == old_wallet_id).first()
            if old_wallet:
                if record.record_type == RecordType.EXPENSE:
                    old_wallet.balance += old_amount
                else:
                    old_wallet.balance -= old_amount

        # Apply new transaction
        if record.wallet_id:
            wallet = db.query(Wallet).filter(Wallet.id == record.wallet_id).first()
            if wallet:
                if record.record_type == RecordType.EXPENSE:
                    wallet.balance -= record.amount
                else:
                    wallet.balance += record.amount
                db.add(wallet)

    db.commit()
    db.refresh(record)

    return record_to_response(record)


@router.delete("/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(Record).filter(
        Record.id == record_id,
        Record.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    # Reverse wallet balance if confirmed
    if record.status == RecordStatus.CONFIRMED and record.wallet_id:
        wallet = db.query(Wallet).filter(Wallet.id == record.wallet_id).first()
        if wallet:
            if record.record_type == RecordType.EXPENSE:
                wallet.balance += record.amount
            else:
                wallet.balance -= record.amount
            db.add(wallet)

    db.delete(record)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{record_id}/confirm", response_model=RecordResponse)
def confirm_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(Record).options(
        joinedload(Record.wallet),
        joinedload(Record.category)
    ).filter(
        Record.id == record_id,
        Record.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    if record.status != RecordStatus.PENDING:
        raise HTTPException(status_code=400, detail="只能确认待确认状态的记录")

    record.status = RecordStatus.CONFIRMED

    # Update wallet balance
    if record.wallet_id:
        wallet = db.query(Wallet).filter(Wallet.id == record.wallet_id).first()
        if wallet:
            if record.record_type == RecordType.EXPENSE:
                wallet.balance -= record.amount
            else:
                wallet.balance += record.amount
            db.add(wallet)

    db.commit()
    db.refresh(record)

    return record_to_response(record)


@router.post("/{record_id}/reject", response_model=dict)
def reject_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(Record).filter(
        Record.id == record_id,
        Record.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    if record.status != RecordStatus.PENDING:
        raise HTTPException(status_code=400, detail="只能拒绝待确认状态的记录")

    record.status = RecordStatus.REJECTED
    db.commit()

    return {"message": "已拒绝该记录"}
