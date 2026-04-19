"""
API tests for wallet endpoints.
"""
import pytest


def test_list_wallets_empty(client, auth_headers):
    """Test listing wallets when none exist."""
    response = client.get("/api/v1/wallets", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_wallets(client, auth_headers, test_wallet):
    """Test listing wallets."""
    response = client.get("/api/v1/wallets", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "测试钱包"
    assert data[0]["balance"] == 1000.00


def test_create_wallet(client, auth_headers):
    """Test creating a wallet."""
    response = client.post(
        "/api/v1/wallets",
        headers=auth_headers,
        json={
            "name": "银行卡",
            "wallet_type": "bank_card",
            "balance": 5000.00,
            "currency": "CNY",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "银行卡"
    assert data["wallet_type"] == "bank_card"
    assert data["balance"] == 5000.00


def test_get_wallet(client, auth_headers, test_wallet):
    """Test getting a specific wallet."""
    response = client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "测试钱包"


def test_get_wallet_not_found(client, auth_headers):
    """Test getting a nonexistent wallet."""
    response = client.get("/api/v1/wallets/9999", headers=auth_headers)
    assert response.status_code == 404


def test_update_wallet(client, auth_headers, test_wallet):
    """Test updating a wallet."""
    response = client.put(
        f"/api/v1/wallets/{test_wallet.id}",
        headers=auth_headers,
        json={"name": "新钱包名", "balance": 2000.00},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "新钱包名"
    assert data["balance"] == 2000.00


def test_delete_wallet(client, auth_headers, test_wallet):
    """Test deleting a wallet."""
    response = client.delete(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers)
    assert response.status_code == 200
    
    # Verify it's deleted
    response = client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers)
    assert response.status_code == 404


def test_transfer_success(client, auth_headers, db, test_user):
    """Test successful transfer between wallets."""
    # Create two wallets
    wallet1 = {
        "name": "钱包1",
        "wallet_type": "cash",
        "balance": 1000.00,
    }
    wallet2 = {
        "name": "钱包2",
        "wallet_type": "cash",
        "balance": 500.00,
    }
    resp1 = client.post("/api/v1/wallets", headers=auth_headers, json=wallet1)
    resp2 = client.post("/api/v1/wallets", headers=auth_headers, json=wallet2)
    
    w1_id = resp1.json()["id"]
    w2_id = resp2.json()["id"]
    
    # Transfer
    response = client.post(
        "/api/v1/wallets/transfer",
        headers=auth_headers,
        json={
            "from_wallet_id": w1_id,
            "to_wallet_id": w2_id,
            "amount": 300.00,
            "note": "测试转账",
        },
    )
    assert response.status_code == 200
    
    # Verify balances
    r1 = client.get(f"/api/v1/wallets/{w1_id}", headers=auth_headers)
    r2 = client.get(f"/api/v1/wallets/{w2_id}", headers=auth_headers)
    assert r1.json()["balance"] == 700.00
    assert r2.json()["balance"] == 800.00


def test_transfer_insufficient_balance(client, auth_headers, db, test_user):
    """Test transfer with insufficient balance."""
    wallet1 = {"name": "钱包1", "wallet_type": "cash", "balance": 100.00}
    wallet2 = {"name": "钱包2", "wallet_type": "cash", "balance": 0}
    resp1 = client.post("/api/v1/wallets", headers=auth_headers, json=wallet1)
    resp2 = client.post("/api/v1/wallets", headers=auth_headers, json=wallet2)
    
    response = client.post(
        "/api/v1/wallets/transfer",
        headers=auth_headers,
        json={
            "from_wallet_id": resp1.json()["id"],
            "to_wallet_id": resp2.json()["id"],
            "amount": 500.00,
        },
    )
    assert response.status_code == 400
    assert "余额不足" in response.json()["detail"]
