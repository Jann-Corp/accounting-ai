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
