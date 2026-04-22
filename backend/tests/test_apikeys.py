"""
API tests for API key endpoints.
"""
import pytest
from datetime import datetime, timedelta


def test_list_api_keys_empty(client, auth_headers):
    """Test listing API keys when none exist."""
    response = client.get("/api/v1/api-keys", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_create_api_key(client, auth_headers):
    """Test creating a new API key."""
    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={
            "name": "测试密钥",
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试密钥"
    assert data["key_prefix"].startswith("ak_")
    assert data["key_full"] is not None  # Full key only returned once
    assert data["is_active"] is True


def test_create_api_key_no_expiry(client, auth_headers):
    """Test creating API key without expiry."""
    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "永久密钥"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "永久密钥"
    assert data["expires_at"] is None


def test_list_api_keys(client, auth_headers, db, test_user):
    """Test listing API keys."""
    from app.models.apikey import ApiKey
    import hashlib
    
    key = ApiKey(
        user_id=test_user.id,
        name="已有密钥",
        key_hash=hashlib.sha256(b"test_key").hexdigest(),
        key_prefix="ak_test",
        is_active=True,
    )
    db.add(key)
    db.commit()
    
    response = client.get("/api/v1/api-keys", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(k["name"] == "已有密钥" for k in data)
    # Full key should not be returned in list
    assert all(k["key_full"] is None for k in data)


def test_update_api_key(client, auth_headers, db, test_user):
    """Test updating an API key."""
    from app.models.apikey import ApiKey
    import hashlib
    
    key = ApiKey(
        user_id=test_user.id,
        name="旧名称",
        key_hash=hashlib.sha256(b"unique_test_key_1").hexdigest(),
        key_prefix="ak_test1",
        is_active=True,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    
    response = client.patch(
        f"/api/v1/api-keys/{key.id}",
        headers=auth_headers,
        json={"name": "新名称"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "新名称"


def test_update_api_key_deactivate(client, auth_headers, db, test_user):
    """Test deactivating an API key."""
    from app.models.apikey import ApiKey
    import hashlib
    
    key = ApiKey(
        user_id=test_user.id,
        name="测试密钥",
        key_hash=hashlib.sha256(b"unique_test_key_2").hexdigest(),
        key_prefix="ak_test2",
        is_active=True,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    
    response = client.patch(
        f"/api/v1/api-keys/{key.id}",
        headers=auth_headers,
        json={"is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


def test_delete_api_key(client, auth_headers, db, test_user):
    """Test deleting an API key."""
    from app.models.apikey import ApiKey
    import hashlib
    
    key = ApiKey(
        user_id=test_user.id,
        name="待删除密钥",
        key_hash=hashlib.sha256(b"unique_test_key_3").hexdigest(),
        key_prefix="ak_test3",
        is_active=True,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    
    response = client.delete(
        f"/api/v1/api-keys/{key.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "API key deleted"
    
    # Verify it's deleted
    response = client.get("/api/v1/api-keys", headers=auth_headers)
    assert key.id not in [k["id"] for k in response.json()]


def test_delete_api_key_not_found(client, auth_headers):
    """Test deleting nonexistent API key."""
    response = client.delete(
        "/api/v1/api-keys/99999",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_update_api_key_not_found(client, auth_headers):
    """Test updating nonexistent API key."""
    response = client.patch(
        "/api/v1/api-keys/99999",
        headers=auth_headers,
        json={"name": "新名称"},
    )
    assert response.status_code == 404


def test_api_key_cannot_access_other_user_keys(client, auth_headers, db, test_user):
    """Test that user cannot access another user's API keys."""
    from app.models.apikey import ApiKey
    from app.models.user import User
    from app.core.security import get_password_hash
    import hashlib
    import time

    # Create another user (unique username!)
    username = f"otheruser_{int(time.time() * 1000)}"
    other_user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=get_password_hash("password"),
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    # Create API key for other user
    key = ApiKey(
        user_id=other_user.id,
        name="其他用户的密钥",
        key_hash=hashlib.sha256(f"unique_test_key_4_{int(time.time() * 1000)}".encode()).hexdigest(),
        key_prefix="ak_test4",
        is_active=True,
    )
    db.add(key)
    db.commit()
    
    # Try to update other user's key
    response = client.patch(
        f"/api/v1/api-keys/{key.id}",
        headers=auth_headers,
        json={"name": "被篡改的名称"},
    )
    assert response.status_code == 404


def test_use_api_key_for_export(client, db, test_user, test_wallet, test_category):
    """Test using API key for authentication on export endpoint."""
    from app.models.apikey import ApiKey
    from app.models.record import Record, RecordType, RecordStatus
    import hashlib
    
    # Create API key
    full_key = "ak_test_export_key_12345"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    api_key = ApiKey(
        user_id=test_user.id,
        name="导出专用密钥",
        key_hash=key_hash,
        key_prefix=full_key[:12],
        is_active=True,
    )
    db.add(api_key)
    
    # Create a record
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        category_id=test_category.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        note="测试记录",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    
    # Use API key for export
    response = client.get(
        "/api/v1/records/export?format=json",
        headers={"X-API-Key": full_key},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


def test_use_invalid_api_key(client):
    """Test using invalid API key."""
    response = client.get(
        "/api/v1/records/export?format=json",
        headers={"X-API-Key": "invalid_key"},
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


def test_use_expired_api_key(client, auth_headers, db, test_user):
    """Test using expired API key."""
    from app.models.apikey import ApiKey
    import hashlib
    
    full_key = "ak_test_expired_key"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    api_key = ApiKey(
        user_id=test_user.id,
        name="过期密钥",
        key_hash=key_hash,
        key_prefix=full_key[:12],
        is_active=True,
        expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
    )
    db.add(api_key)
    db.commit()
    
    response = client.get(
        "/api/v1/records/export?format=json",
        headers={"X-API-Key": full_key},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"]
