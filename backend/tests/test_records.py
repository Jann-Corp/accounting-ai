"""
API tests for record endpoints.
"""
import pytest
from datetime import datetime


def test_list_records_empty(client, auth_headers):
    """Test listing records when none exist."""
    response = client.get("/api/v1/records", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_records(client, auth_headers, db, test_user, test_wallet, test_category):
    """Test listing records."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        note="测试消费",
        date=datetime.utcnow(),
        status=RecordStatus.CONFIRMED,
    )
    db.add(record)
    db.commit()
    
    response = client.get("/api/v1/records", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == 100.00


def test_create_record(client, auth_headers, test_wallet, test_category):
    """Test creating a record."""
    response = client.post(
        "/api/v1/records",
        headers=auth_headers,
        json={
            "wallet_id": test_wallet.id,
            "category_id": test_category.id,
            "amount": 50.00,
            "record_type": "expense",
            "note": "午餐",
            "date": datetime.utcnow().isoformat(),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 50.00
    assert data["note"] == "午餐"


def test_create_record_updates_balance(client, auth_headers, test_wallet, test_category):
    """Test that creating a record updates wallet balance."""
    initial_balance = test_wallet.balance
    
    client.post(
        "/api/v1/records",
        headers=auth_headers,
        json={
            "wallet_id": test_wallet.id,
            "category_id": test_category.id,
            "amount": 100.00,
            "record_type": "expense",
            "note": "测试",
            "date": datetime.utcnow().isoformat(),
        },
    )
    
    # Check updated balance
    response = client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers)
    assert response.json()["balance"] == initial_balance - 100.00


def test_get_pending_records(client, auth_headers, db, test_user, test_wallet):
    """Test listing pending records."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=200.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        note="待确认",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    
    response = client.get("/api/v1/records/pending", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "pending"


def test_confirm_record(client, auth_headers, db, test_user, test_wallet):
    """Test confirming a pending record."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=300.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        note="待确认消费",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    response = client.post(
        f"/api/v1/records/{record.id}/confirm",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_reject_record(client, auth_headers, db, test_user, test_wallet):
    """Test rejecting a pending record."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=300.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        note="待确认消费",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    response = client.post(
        f"/api/v1/records/{record.id}/reject",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "已拒绝" in response.json()["message"]


def test_delete_record(client, auth_headers, db, test_user, test_wallet):
    """Test deleting a record."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=50.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        note="删除测试",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    response = client.delete(
        f"/api/v1/records/{record.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200


def test_create_record_with_income(client, auth_headers, test_wallet, test_category):
    """Test creating an income record."""
    response = client.post(
        "/api/v1/records",
        headers=auth_headers,
        json={
            "wallet_id": test_wallet.id,
            "category_id": test_category.id,
            "amount": 5000.00,
            "record_type": "income",
            "note": "工资",
            "date": datetime.utcnow().isoformat(),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 5000.00
    assert data["record_type"] == "income"


def test_create_record_with_invalid_wallet(client, auth_headers, test_category):
    """Test creating a record with non-existent wallet."""
    response = client.post(
        "/api/v1/records",
        headers=auth_headers,
        json={
            "wallet_id": 99999,
            "category_id": test_category.id,
            "amount": 100.00,
            "record_type": "expense",
            "date": datetime.utcnow().isoformat(),
        },
    )
    assert response.status_code == 404
    assert "账户不存在" in response.json()["detail"]


def test_list_records_with_date_filter(client, auth_headers, db, test_user, test_wallet):
    """Test listing records with date filter."""
    from app.models.record import Record, RecordType, RecordStatus
    
    # Create record today
    today_record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        date=datetime.utcnow(),
    )
    # Create record yesterday
    yesterday_record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=200.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        date=datetime.utcnow().replace(day=datetime.utcnow().day - 1 if datetime.utcnow().day > 1 else 28),
    )
    db.add(today_record)
    db.add(yesterday_record)
    db.commit()
    
    # Filter by today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    response = client.get(
        f"/api/v1/records?start_date={today_start.isoformat()}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(r["amount"] == 100.00 for r in data)


def test_list_records_with_type_filter(client, auth_headers, db, test_user, test_wallet):
    """Test listing records with type filter."""
    from app.models.record import Record, RecordType, RecordStatus
    
    # Create expense record
    expense_record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        date=datetime.utcnow(),
    )
    # Create income record
    income_record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=500.00,
        record_type=RecordType.INCOME,
        status=RecordStatus.CONFIRMED,
        date=datetime.utcnow(),
    )
    db.add(expense_record)
    db.add(income_record)
    db.commit()
    
    # Filter by expense type
    response = client.get(
        "/api/v1/records?record_type=expense",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Response uses "record_type" field, not "type"
    assert all(r["record_type"] == "expense" for r in data)


def test_list_records_with_status_filter(client, auth_headers, db, test_user, test_wallet):
    """Test listing records with status filter."""
    from app.models.record import Record, RecordType, RecordStatus
    
    # Create confirmed record
    confirmed_record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        date=datetime.utcnow(),
    )
    # Create pending record
    pending_record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=200.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        date=datetime.utcnow(),
    )
    db.add(confirmed_record)
    db.add(pending_record)
    db.commit()
    
    # Filter by pending status
    response = client.get(
        "/api/v1/records?status=pending",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(r["status"] == "pending" for r in data)


def test_list_records_pagination(client, auth_headers, db, test_user, test_wallet):
    """Test listing records with pagination."""
    from app.models.record import Record, RecordType, RecordStatus
    
    # Create multiple records
    for i in range(5):
        record = Record(
            user_id=test_user.id,
            wallet_id=test_wallet.id,
            amount=100.00 + i,
            record_type=RecordType.EXPENSE,
            status=RecordStatus.CONFIRMED,
            date=datetime.utcnow(),
        )
        db.add(record)
    db.commit()
    
    # Test limit
    response = client.get(
        "/api/v1/records?limit=2",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_record_not_found(client, auth_headers):
    """Test getting a non-existent record."""
    response = client.get(
        "/api/v1/records/99999",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert "记录不存在" in response.json()["detail"]


def test_update_record(client, auth_headers, db, test_user, test_wallet):
    """Test updating a record."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        note="原始备注",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    response = client.put(
        f"/api/v1/records/{record.id}",
        headers=auth_headers,
        json={
            "amount": 200.00,
            "note": "更新后的备注",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 200.00
    assert data["note"] == "更新后的备注"


def test_delete_record_not_found(client, auth_headers):
    """Test deleting a non-existent record."""
    response = client.delete(
        "/api/v1/records/99999",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert "记录不存在" in response.json()["detail"]


def test_confirm_record_not_pending(client, auth_headers, db, test_user, test_wallet):
    """Test confirming a record that is not pending."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,  # Already confirmed
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    response = client.post(
        f"/api/v1/records/{record.id}/confirm",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "只能确认待确认状态" in response.json()["detail"]


def test_reject_record_not_pending(client, auth_headers, db, test_user, test_wallet):
    """Test rejecting a record that is not pending."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.REJECTED,  # Already rejected
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    response = client.post(
        f"/api/v1/records/{record.id}/reject",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "只能拒绝待确认状态" in response.json()["detail"]
