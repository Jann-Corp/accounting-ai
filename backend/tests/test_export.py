"""
API tests for export endpoints.
"""
import pytest
import csv
import json
import io
from datetime import datetime, timedelta


def test_export_csv_empty(client, auth_headers):
    """Test CSV export with no records."""
    response = client.get(
        "/api/v1/records/export?format=csv",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "records_" in response.headers["content-disposition"]
    assert ".csv" in response.headers["content-disposition"]

    # Parse CSV content
    content = response.content.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1  # Only header row
    assert rows[0] == ["ID", "日期", "类型", "金额", "账户", "分类", "备注", "AI置信度", "状态", "创建时间"]


def test_export_json_empty(client, auth_headers):
    """Test JSON export with no records."""
    response = client.get(
        "/api/v1/records/export?format=json",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "records_" in response.headers["content-disposition"]
    assert ".json" in response.headers["content-disposition"]
    
    data = response.json()
    assert data == []


def test_export_csv_with_records(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test CSV export with records."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=100.50,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        note="测试消费",
        date=datetime.utcnow(),
        ai_confidence=0.95,
    )
    db.add(record)
    db.commit()
    
    response = client.get(
        "/api/v1/records/export?format=csv",
        headers=auth_headers,
    )
    assert response.status_code == 200
    
    content = response.content.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 2  # Header + 1 record
    assert rows[1][3] == "100.5"  # Amount
    assert rows[1][6] == "测试消费"  # Note


def test_export_json_with_records(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test JSON export with records."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=200.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        note="测试记录",
        date=datetime.utcnow(),
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
    assert data[0]["amount"] == 200.0
    assert data[0]["note"] == "测试记录"
    assert data[0]["type"] == "expense"


def test_export_with_date_filter(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test export with date range filter."""
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
        status=RecordStatus.CONFIRMED,
        date=yesterday,
    )
    record2 = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=200.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        date=today,
    )
    db.add(record1)
    db.add(record2)
    db.commit()
    
    # Filter by today only
    start = today.strftime("%Y-%m-%d")
    response = client.get(
        f"/api/v1/records/export?format=json&start_date={start}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == 200.00


def test_export_with_type_filter(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test export with record type filter."""
    from app.models.record import Record, RecordType, RecordStatus
    
    expense = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        date=datetime.utcnow(),
    )
    income = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=500.00,
        record_type=RecordType.INCOME,
        status=RecordStatus.CONFIRMED,
        date=datetime.utcnow(),
    )
    db.add(expense)
    db.add(income)
    db.commit()
    
    # Filter by expense only
    response = client.get(
        "/api/v1/records/export?format=json&record_type=expense",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == 100.00
    assert data[0]["type"] == "expense"


def test_export_with_invalid_format(client, auth_headers):
    """Test export with invalid format."""
    response = client.get(
        "/api/v1/records/export?format=xml",
        headers=auth_headers,
    )
    assert response.status_code == 422  # Validation error


def test_export_unauthenticated(client):
    """Test export without authentication."""
    response = client.get("/api/v1/records/export?format=csv")
    assert response.status_code == 401


def test_export_csv_special_characters(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test CSV export with special characters in data."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        note='测试，带逗号，和"引号"',
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    
    response = client.get(
        "/api/v1/records/export?format=csv",
        headers=auth_headers,
    )
    assert response.status_code == 200
    
    # Should not raise CSV parsing error
    content = response.content.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 2


def test_export_json_unicode(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test JSON export with Unicode characters."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        note="中文测试 日本語テスト 한국어 테스트",
        date=datetime.utcnow(),
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
    assert "中文测试" in data[0]["note"]
    assert "日本語" in data[0]["note"]


def test_export_multiple_records_ordering(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test that export returns records in descending date order."""
    from app.models.record import Record, RecordType, RecordStatus

    base_date = datetime.utcnow()

    for i in range(5):
        record = Record(
            user_id=test_user.id,
            wallet_id=test_wallet.id,
            category_id=test_category.id,
            amount=float(i + 1),
            record_type=RecordType.EXPENSE,
            status=RecordStatus.CONFIRMED,
            date=base_date - timedelta(days=i),
        )
        db.add(record)
    db.commit()

    response = client.get(
        "/api/v1/records/export?format=json",
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 5
    # Should be ordered by date descending (newest first): i=0 (date=today, amount=1.0) first!
    assert data[0]["amount"] == 1.0  # Most recent
    assert data[4]["amount"] == 5.0  # Oldest
