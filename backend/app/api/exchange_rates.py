from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.exchange_rate import ExchangeRate
from app.models.user import User
from app.schemas.exchange_rate import ExchangeRateCreate, ExchangeRateUpdate, ExchangeRateResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/exchange-rates", tags=["汇率管理"])


@router.get("", response_model=List[ExchangeRateResponse])
def list_exchange_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户所有自定义汇率"""
    rates = db.query(ExchangeRate).filter(ExchangeRate.user_id == current_user.id).all()
    return rates


@router.post("", response_model=ExchangeRateResponse)
def create_or_update_exchange_rate(
    data: ExchangeRateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建或更新某个货币的汇率（upsert）"""
    existing = db.query(ExchangeRate).filter(
        ExchangeRate.user_id == current_user.id,
        ExchangeRate.currency == data.currency.upper(),
    ).first()

    if existing:
        existing.rate = data.rate
    else:
        existing = ExchangeRate(
            user_id=current_user.id,
            currency=data.currency.upper(),
            rate=data.rate,
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)
    return existing


@router.delete("/{currency}")
def delete_exchange_rate(
    currency: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除某个货币的汇率，恢复使用默认汇率"""
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.user_id == current_user.id,
        ExchangeRate.currency == currency.upper(),
    ).first()

    if not rate:
        raise HTTPException(status_code=404, detail="该货币汇率不存在")

    db.delete(rate)
    db.commit()
    return {"message": f"已删除 {currency.upper()} 汇率"}
