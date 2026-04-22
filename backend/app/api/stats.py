from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from calendar import monthrange

from app.database import get_db
from app.models.record import Record, RecordType, RecordStatus
from app.models.category import Category
from app.schemas.stats import MonthlyStats, CategoryBreakdown, CategoryBreakdownResponse, TrendPoint, TrendResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/monthly", response_model=MonthlyStats)
def get_monthly_stats(
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if year is None:
        year = datetime.utcnow().year
    if month is None:
        month = datetime.utcnow().month
    
    # Calculate date range for the month
    _, last_day = monthrange(year, month)
    start_date = datetime(year, month, 1, 0, 0, 0)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    print(f"DEBUG STATS QUERY: user_id={current_user.id}, year={year}, month={month}, start_date={start_date}, end_date={end_date}", flush=True)
    
    # Query records
    records = db.query(Record).filter(
        Record.user_id == current_user.id,
        Record.status == RecordStatus.CONFIRMED,
        Record.date >= start_date,
        Record.date <= end_date
    ).all()
    
    print(f"DEBUG STATS RESULT: found {len(records)} records", flush=True)
    for r in records:
        print(f"  - record id={r.id}, amount={r.amount}, type={r.record_type}, date={r.date}, status={r.status}", flush=True)
    
    total_expense = sum(r.amount for r in records if r.record_type == RecordType.EXPENSE)
    total_income = sum(r.amount for r in records if r.record_type == RecordType.INCOME)
    
    return MonthlyStats(
        year=year,
        month=month,
        total_expense=total_expense,
        total_income=total_income,
        balance=total_income - total_expense,
        record_count=len(records)
    )


@router.get("/category-breakdown", response_model=CategoryBreakdownResponse)
def get_category_breakdown(
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if year is None:
        year = datetime.utcnow().year
    if month is None:
        month = datetime.utcnow().month
    
    # Calculate date range for the month
    _, last_day = monthrange(year, month)
    start_date = datetime(year, month, 1, 0, 0, 0)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    # Query with aggregation
    results = db.query(
        Category.id,
        Category.name,
        Category.icon,
        func.sum(Record.amount).label("total"),
        func.count(Record.id).label("count")
    ).join(
        Record, Record.category_id == Category.id
    ).filter(
        Record.user_id == current_user.id,
        Record.status == RecordStatus.CONFIRMED,
        Record.record_type == RecordType.EXPENSE,
        Record.date >= start_date,
        Record.date <= end_date
    ).group_by(
        Category.id, Category.name, Category.icon
    ).all()
    
    total_expense = sum(r.total for r in results) if results else 0
    
    breakdown = []
    for r in results:
        breakdown.append(CategoryBreakdown(
            category_id=r.id,
            category_name=r.name,
            category_icon=r.icon,
            total_amount=r.total or 0,
            percentage=(r.total / total_expense * 100) if total_expense > 0 else 0,
            record_count=r.count
        ))
    
    # Sort by total amount descending
    breakdown.sort(key=lambda x: x.total_amount, reverse=True)
    
    return CategoryBreakdownResponse(
        year=year,
        month=month,
        breakdown=breakdown
    )


@router.get("/trend", response_model=TrendResponse)
def get_trend(
    months: int = Query(default=6, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    trend = []
    
    for i in range(months - 1, -1, -1):
        # Calculate month
        month_date = datetime(now.year, now.month, 1)
        if i > 0:
            # Go back i months
            year = now.year
            m = now.month - i
            while m <= 0:
                m += 12
                year -= 1
            month_date = datetime(year, m, 1)
        
        _, last_day = monthrange(month_date.year, month_date.month)
        start_date = datetime(month_date.year, month_date.month, 1, 0, 0, 0)
        end_date = datetime(month_date.year, month_date.month, last_day, 23, 59, 59)
        
        records = db.query(Record).filter(
            Record.user_id == current_user.id,
            Record.status == RecordStatus.CONFIRMED,
            Record.date >= start_date,
            Record.date <= end_date
        ).all()
        
        total_expense = sum(r.amount for r in records if r.record_type == RecordType.EXPENSE)
        total_income = sum(r.amount for r in records if r.record_type == RecordType.INCOME)
        
        trend.append(TrendPoint(
            year=month_date.year,
            month=month_date.month,
            total_expense=total_expense,
            total_income=total_income
        ))
    
    return TrendResponse(trend=trend)
