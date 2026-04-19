from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.wallet import Wallet, WalletType
from app.models.record import Record, RecordType, RecordStatus
from app.schemas.wallet import WalletCreate, WalletUpdate, WalletResponse, TransferRequest
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/wallets", tags=["账户"])


@router.get("", response_model=List[WalletResponse])
def list_wallets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Wallet).filter(Wallet.user_id == current_user.id).order_by(Wallet.created_at).all()


@router.post("", response_model=WalletResponse)
def create_wallet(
    wallet_data: WalletCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = Wallet(
        user_id=current_user.id,
        name=wallet_data.name,
        wallet_type=wallet_data.wallet_type,
        balance=wallet_data.balance,
        currency=wallet_data.currency,
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/{wallet_id}", response_model=WalletResponse)
def get_wallet(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(
        Wallet.id == wallet_id,
        Wallet.user_id == current_user.id
    ).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="账户不存在")
    return wallet


@router.put("/{wallet_id}", response_model=WalletResponse)
def update_wallet(
    wallet_id: int,
    wallet_data: WalletUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(
        Wallet.id == wallet_id,
        Wallet.user_id == current_user.id
    ).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    if wallet_data.name is not None:
        wallet.name = wallet_data.name
    if wallet_data.wallet_type is not None:
        wallet.wallet_type = wallet_data.wallet_type
    if wallet_data.balance is not None:
        wallet.balance = wallet_data.balance
    if wallet_data.currency is not None:
        wallet.currency = wallet_data.currency
    
    db.commit()
    db.refresh(wallet)
    return wallet


@router.delete("/{wallet_id}")
def delete_wallet(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(
        Wallet.id == wallet_id,
        Wallet.user_id == current_user.id
    ).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="账户不存在")
    
    db.delete(wallet)
    db.commit()
    return {"message": "删除成功"}


@router.post("/transfer", response_model=dict)
def transfer_between_wallets(
    transfer_data: TransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check source wallet
    from_wallet = db.query(Wallet).filter(
        Wallet.id == transfer_data.from_wallet_id,
        Wallet.user_id == current_user.id
    ).first()
    if not from_wallet:
        raise HTTPException(status_code=404, detail="源账户不存在")
    
    # Check target wallet
    to_wallet = db.query(Wallet).filter(
        Wallet.id == transfer_data.to_wallet_id,
        Wallet.user_id == current_user.id
    ).first()
    if not to_wallet:
        raise HTTPException(status_code=404, detail="目标账户不存在")
    
    if from_wallet.balance < transfer_data.amount:
        raise HTTPException(status_code=400, detail="余额不足")
    
    now = datetime.utcnow()
    
    # Create expense record from source
    expense_record = Record(
        user_id=current_user.id,
        wallet_id=from_wallet.id,
        amount=transfer_data.amount,
        record_type=RecordType.EXPENSE,
        note=f"转账至 {to_wallet.name}" + (f" - {transfer_data.note}" if transfer_data.note else ""),
        date=now,
        status=RecordStatus.CONFIRMED,
    )
    db.add(expense_record)
    
    # Create income record to target
    income_record = Record(
        user_id=current_user.id,
        wallet_id=to_wallet.id,
        amount=transfer_data.amount,
        record_type=RecordType.INCOME,
        note=f"转账来自 {from_wallet.name}" + (f" - {transfer_data.note}" if transfer_data.note else ""),
        date=now,
        status=RecordStatus.CONFIRMED,
    )
    db.add(income_record)
    
    # Update balances
    from_wallet.balance -= transfer_data.amount
    to_wallet.balance += transfer_data.amount
    
    db.commit()
    return {"message": "转账成功"}
