"""
API tests for stats endpoints.
"""
import pytest
from datetime import datetime


def test_monthly_stats_empty(client, auth_headers):
    """Test monthly stats with no records."""
    response = client.get("/api/v1/stats/monthly", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_expense"] == 0
    assert data["total_income"] == 0


def test_monthly_stats_with_records(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test monthly stats with records."""
    from app.models.record import Record, RecordType, RecordStatus
    
    # Add expense
    expense = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=500.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        note="购物",
        date=datetime.utcnow(),
    )
    db.add(expense)
    
    # Add income
    income = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=1000.00,
        record_type=RecordType.INCOME,
        status=RecordStatus.CONFIRMED,
        note="工资",
        date=datetime.utcnow(),
    )
    db.add(income)
    db.commit()
    
    response = client.get("/api/v1/stats/monthly", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_expense"] == 500.00
    assert data["total_income"] == 1000.00
    assert data["balance"] == 500.00
    assert data["record_count"] == 2


def test_category_breakdown(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test category breakdown stats."""
    from app.models.record import Record, RecordType, RecordStatus
    
    for i in range(3):
        record = Record(
            user_id=test_user.id,
            wallet_id=test_wallet.id,
            category_id=test_category.id,
            amount=100.00,
            record_type=RecordType.EXPENSE,
            status=RecordStatus.CONFIRMED,
            note=f"消费{i+1}",
            date=datetime.utcnow(),
        )
        db.add(record)
    db.commit()
    
    response = client.get("/api/v1/stats/category-breakdown", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["breakdown"]) == 1
    assert data["breakdown"][0]["total_amount"] == 300.00
    assert data["breakdown"][0]["record_count"] == 3


def test_trend(client, auth_headers):
    """Test trend endpoint."""
    response = client.get("/api/v1/stats/trend?months=3", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["trend"]) == 3
