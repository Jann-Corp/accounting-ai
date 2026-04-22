"""
API tests for export endpoints.
"""
import pytest
from datetime import datetime, timedelta
import csv
import io
import json


def test_export_csv_empty(client, auth_headers):
    """Test exporting CSV with no records."""
    response = client.get(
        "/api/v1/records/export?format=csv",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Content-Disposition" in response.headers
    assert ".csv" in response.headers["Content-Disposition"]
    
    # Check CSV content has header row only
    content = response.content.decode("utf-8")
    lines = content.strip().split("\n")
    assert len(lines) == 1  # Header row only
    assert "ID" in lines[0]
    assert "日期" in lines[0]
    assert "金额" in lines[0]


def test_export_csv_with_records(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test exporting CSV with records."""
    from app.models.record import Record, RecordType, RecordStatus
    
    # Create test records
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=100.50,
        record_type=RecordType.EXPENSE,
        note="测试导出",
        date=datetime.utcnow(),
        status=RecordStatus.CONFIRMED,
    )
    db.add(record)
    db.commit()
    
    response = client.get(
        "/api/v1/records/export?format=csv",
        headers=auth_headers,
    )
    assert response.status_code == 200
    
    content = response.content.decode("utf-8")
    lines = content.strip().split("\n")
    assert len(lines) == 2  # Header + 1 record
    
    # Parse CSV
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[1][3] == "100.5"  # Amount column


def test_export_json_empty(client, auth_headers):
    """Test exporting JSON with no records."""
    response = client.get(
        "/api/v1/records/export?format=json",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert ".json" in response.headers["Content-Disposition"]
    
    data = response.json()
    assert data == []


def test_export_json_with_records(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test exporting JSON with records."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=200.00,
        record_type=RecordType.INCOME,
        note="JSON 测试",
        date=datetime.utcnow(),
        status=RecordStatus.CONFIRMED,
    )
    db.add(record)
    db.commit()
    
    response = client.get(
        "/api/v1/records/export?format=json",
        headers=auth_headers,
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == 200.00
    assert data[0]["type"] == "income"
    assert data[0]["note"] == "JSON 测试"


def test_export_filter_by_date(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test exporting with date filters."""
    from app.models.record import Record, RecordType, RecordStatus
    
    # Create records on different dates
    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)
    
    record1 = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        date=yesterday,
        status=RecordStatus.CONFIRMED,
    )
    record2 = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=200.00,
        record_type=RecordType.EXPENSE,
        date=today,
        status=RecordStatus.CONFIRMED,
    )
    db.add(record1)
    db.add(record2)
    db.commit()
    
    # Filter by start_date (should only get today's record)
    response = client.get(
        f"/api/v1/records/export?format=json&start_date={today.strftime('%Y-%m-%d')}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == 200.00


def test_export_filter_by_type(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test exporting with record type filter."""
    from app.models.record import Record, RecordType, RecordStatus
    
    expense = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=50.00,
        record_type=RecordType.EXPENSE,
        date=datetime.utcnow(),
        status=RecordStatus.CONFIRMED,
    )
    income = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=500.00,
        record_type=RecordType.INCOME,
        date=datetime.utcnow(),
        status=RecordStatus.CONFIRMED,
    )
    db.add(expense)
    db.add(income)
    db.commit()
    
    # Filter by expense type
    response = client.get(
        "/api/v1/records/export?format=json&record_type=expense",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "expense"
    assert data[0]["amount"] == 50.00


def test_export_unauthorized(client):
    """Test export without authentication."""
    response = client.get("/api/v1/records/export?format=csv")
    assert response.status_code == 401


def test_export_invalid_format(client, auth_headers):
    """Test export with invalid format."""
    response = client.get(
        "/api/v1/records/export?format=xml",
        headers=auth_headers,
    )
    # The regex in the endpoint should reject invalid formats
    assert response.status_code == 422 or response.status_code == 400


def test_export_csv_headers(client, auth_headers):
    """Test CSV export has correct headers."""
    response = client.get(
        "/api/v1/records/export?format=csv",
        headers=auth_headers,
    )
    content = response.content.decode("utf-8")
    header = content.split("\n")[0]
    
    expected_columns = ["ID", "日期", "类型", "金额", "账户", "分类", "备注", "AI置信度", "状态", "创建时间"]
    for col in expected_columns:
        assert col in header, f"Missing column: {col}"
