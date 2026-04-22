"""
API tests for API key endpoints.
"""
import pytest
from datetime import datetime, timedelta


def test_list_api_keys_empty(client, auth_headers):
    """Test listing API keys when none exist."""
    response = client.get("/api/v1/api-keys", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_api_key(client, auth_headers):
    """Test creating a new API key."""
    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "test-key", "expires_at": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-key"
    assert data["key_prefix"].startswith("ak_")
    assert data["key_full"].startswith("ak_")  # Full key only returned at creation
    assert data["is_active"] is True


def test_create_api_key_with_expiry(client, auth_headers):
    """Test creating an API key with expiry date."""
    expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "expiring-key", "expires_at": expires_at},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "expiring-key"
    assert data["expires_at"] is not None


def test_list_api_keys_after_create(client, auth_headers):
    """Test listing API keys after creating one."""
    # Create a key
    client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "list-test-key"},
    )
    
    # List keys
    response = client.get("/api/v1/api-keys", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(k["name"] == "list-test-key" for k in data)
    # Full key should NOT be returned in list
    assert all(k["key_full"] is None for k in data)


def test_update_api_key(client, auth_headers):
    """Test updating an API key."""
    # Create a key
    create_response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "update-test-key"},
    )
    key_id = create_response.json()["id"]
    
    # Update the key
    response = client.patch(
        f"/api/v1/api-keys/{key_id}",
        headers=auth_headers,
        json={"name": "updated-key-name", "is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated-key-name"
    assert data["is_active"] is False


def test_update_api_key_not_found(client, auth_headers):
    """Test updating a nonexistent API key."""
    response = client.patch(
        "/api/v1/api-keys/9999",
        headers=auth_headers,
        json={"name": "nonexistent"},
    )
    assert response.status_code == 404
    assert "API key not found" in response.json()["detail"]


def test_delete_api_key(client, auth_headers):
    """Test deleting an API key."""
    # Create a key
    create_response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "delete-test-key"},
    )
    key_id = create_response.json()["id"]
    
    # Delete the key
    response = client.delete(
        f"/api/v1/api-keys/{key_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "API key deleted"
    
    # Verify it's deleted
    response = client.get("/api/v1/api-keys", headers=auth_headers)
    assert key_id not in [k["id"] for k in response.json()]


def test_delete_api_key_not_found(client, auth_headers):
    """Test deleting a nonexistent API key."""
    response = client.delete(
        "/api/v1/api-keys/9999",
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert "API key not found" in response.json()["detail"]


def test_api_key_authentication(client, auth_headers):
    """Test using API key for authentication on export endpoint."""
    # Create an API key
    create_response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "auth-test-key"},
    )
    api_key = create_response.json()["key_full"]
    
    # Use API key to access export endpoint
    response = client.get(
        "/api/v1/records/export?format=csv",
        headers={"X-API-Key": api_key},
    )
    # Should succeed with valid API key
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


def test_api_key_expired(client, auth_headers, db, test_user):
    """Test that expired API key cannot be used."""
    from app.models.apikey import ApiKey
    import hashlib
    
    # Create an expired API key directly in DB
    expired_time = datetime.utcnow() - timedelta(days=1)
    key_data = "ak_expired_test_key_12345"
    key_hash = hashlib.sha256(key_data.encode()).hexdigest()
    
    api_key = ApiKey(
        user_id=test_user.id,
        name="expired-key",
        key_hash=key_hash,
        key_prefix=key_data[:12],
        expires_at=expired_time,
        is_active=True,
    )
    db.add(api_key)
    db.commit()
    
    # Try to use expired key
    response = client.get(
        "/api/v1/records/export?format=csv",
        headers={"X-API-Key": key_data},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()
