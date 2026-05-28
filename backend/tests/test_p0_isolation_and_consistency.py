"""
P0 安全性 & 数据一致性测试

1. 跨用户数据隔离（越权访问测试）
   - 验证用户B无法访问/修改/删除用户A的 wallet / category / record / apikey
   - 验证用户B无法查看用户A的统计数据

2. 数据一致性（余额回滚测试）
   - 删除已确认的支出记录 → 钱包余额恢复
   - 删除已确认的收入记录 → 钱包余额恢复
   - 更新已确认记录的金额 → 钱包余额正确调整
   - 更新已确认记录的类型（支出↔收入）→ 钱包余额正确调整
"""
import pytest
from datetime import datetime


# ============================================================
# Fixtures: second user for cross-user isolation tests
# ============================================================

@pytest.fixture
def test_user_b(db):
    """Create a second test user for isolation tests."""
    from app.models.user import User
    from app.core.security import get_password_hash
    from tests.conftest import _counter
    _counter[0] += 1
    user = User(
        username=f"user_b_{_counter[0]}",
        email=f"userb{_counter[0]}@example.com",
        hashed_password=get_password_hash("testpass123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers_b(client, test_user_b):
    """Auth headers for user B."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": test_user_b.username, "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# P0-1: 跨用户数据隔离测试
# ============================================================

class TestCrossUserWalletIsolation:
    """用户B不能访问/修改/删除用户A的 Wallet"""

    def test_user_b_cannot_get_user_a_wallet(self, client, auth_headers, auth_headers_b, test_wallet):
        response = client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers_b)
        assert response.status_code == 404

    def test_user_b_cannot_update_user_a_wallet(self, client, auth_headers, auth_headers_b, test_wallet):
        response = client.put(
            f"/api/v1/wallets/{test_wallet.id}",
            headers=auth_headers_b,
            json={"name": "被篡改的名字"},
        )
        assert response.status_code == 404

    def test_user_b_cannot_delete_user_a_wallet(self, client, auth_headers, auth_headers_b, test_wallet):
        response = client.delete(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers_b)
        assert response.status_code == 404

    def test_user_b_cannot_see_user_a_wallet_in_list(self, client, auth_headers, auth_headers_b, test_wallet):
        response = client.get("/api/v1/wallets", headers=auth_headers_b)
        assert response.status_code == 200
        wallet_ids = [w["id"] for w in response.json()]
        assert test_wallet.id not in wallet_ids


class TestCrossUserCategoryIsolation:
    """用户B不能访问/修改/删除用户A的 Category"""

    def test_user_b_cannot_update_user_a_category(self, client, auth_headers, auth_headers_b, test_category):
        response = client.put(
            f"/api/v1/categories/{test_category.id}",
            headers=auth_headers_b,
            json={"name": "被篡改的分类"},
        )
        assert response.status_code == 404

    def test_user_b_cannot_delete_user_a_category(self, client, auth_headers, auth_headers_b, test_category):
        response = client.delete(f"/api/v1/categories/{test_category.id}", headers=auth_headers_b)
        assert response.status_code == 404

    def test_user_b_cannot_see_user_a_categories(self, client, auth_headers, auth_headers_b, test_category):
        response = client.get("/api/v1/categories", headers=auth_headers_b)
        assert response.status_code == 200
        cat_ids = [c["id"] for c in response.json()]
        assert test_category.id not in cat_ids


class TestCrossUserRecordIsolation:
    """用户B不能访问/修改/删除用户A的 Record"""

    def _create_confirmed_record(self, db, test_user, test_wallet):
        from app.models.record import Record, RecordType, RecordStatus
        record = Record(
            user_id=test_user.id,
            wallet_id=test_wallet.id,
            amount=100.00,
            record_type=RecordType.EXPENSE,
            status=RecordStatus.CONFIRMED,
            note="用户A的记录",
            date=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def test_user_b_cannot_get_user_a_record(self, client, auth_headers_b, db, test_user, test_wallet):
        record = self._create_confirmed_record(db, test_user, test_wallet)
        response = client.get(f"/api/v1/records/{record.id}", headers=auth_headers_b)
        assert response.status_code == 404

    def test_user_b_cannot_update_user_a_record(self, client, auth_headers_b, db, test_user, test_wallet):
        record = self._create_confirmed_record(db, test_user, test_wallet)
        response = client.put(f"/api/v1/records/{record.id}", headers=auth_headers_b, json={"amount": 9999.00})
        assert response.status_code == 404

    def test_user_b_cannot_delete_user_a_record(self, client, auth_headers_b, db, test_user, test_wallet):
        record = self._create_confirmed_record(db, test_user, test_wallet)
        response = client.delete(f"/api/v1/records/{record.id}", headers=auth_headers_b)
        assert response.status_code == 404

    def test_user_b_cannot_confirm_user_a_record(self, client, auth_headers_b, db, test_user, test_wallet):
        from app.models.record import Record, RecordType, RecordStatus
        record = Record(
            user_id=test_user.id, wallet_id=test_wallet.id, amount=100.00,
            record_type=RecordType.EXPENSE, status=RecordStatus.PENDING, date=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        response = client.post(f"/api/v1/records/{record.id}/confirm", headers=auth_headers_b)
        assert response.status_code == 404

    def test_user_b_cannot_see_user_a_records(self, client, auth_headers_b, db, test_user, test_wallet):
        self._create_confirmed_record(db, test_user, test_wallet)
        response = client.get("/api/v1/records", headers=auth_headers_b)
        assert response.status_code == 200
        assert response.json() == []


class TestCrossUserApiKeyIsolation:
    """用户B不能访问/修改/删除用户A的 API Key"""

    def test_user_b_cannot_update_user_a_apikey(self, client, auth_headers, auth_headers_b):
        create_resp = client.post("/api/v1/api-keys", headers=auth_headers, json={"name": "user_a_key"})
        key_id = create_resp.json()["id"]
        response = client.patch(f"/api/v1/api-keys/{key_id}", headers=auth_headers_b, json={"name": "hacked_key"})
        assert response.status_code == 404

    def test_user_b_cannot_delete_user_a_apikey(self, client, auth_headers, auth_headers_b):
        create_resp = client.post("/api/v1/api-keys", headers=auth_headers, json={"name": "user_a_key2"})
        key_id = create_resp.json()["id"]
        response = client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_headers_b)
        assert response.status_code == 404

    def test_user_b_cannot_see_user_a_apikeys(self, client, auth_headers, auth_headers_b):
        client.post("/api/v1/api-keys", headers=auth_headers, json={"name": "user_a_key3"})
        response = client.get("/api/v1/api-keys", headers=auth_headers_b)
        assert response.status_code == 200
        key_names = [k["name"] for k in response.json()]
        assert "user_a_key3" not in key_names


class TestCrossUserStatsIsolation:
    """用户B不能通过统计接口看到用户A的数据"""

    def test_user_b_cannot_see_user_a_stats(self, client, auth_headers, auth_headers_b, db, test_user, test_wallet, test_category):
        from app.models.record import Record, RecordType, RecordStatus
        record = Record(
            user_id=test_user.id, wallet_id=test_wallet.id, category_id=test_category.id,
            amount=9999.00, record_type=RecordType.EXPENSE, status=RecordStatus.CONFIRMED,
            date=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        response = client.get("/api/v1/stats/monthly", headers=auth_headers_b)
        assert response.status_code == 200
        data = response.json()
        assert data["total_expense"] == 0
        assert data["total_income"] == 0


# ============================================================
# P0-2: 数据一致性 — 余额回滚测试
# ============================================================

class TestRecordDeleteBalanceRollback:
    """删除已确认记录后，钱包余额应正确恢复"""

    def test_delete_expense_record_restores_balance(self, client, auth_headers, test_wallet, test_category):
        initial_balance = 1000.00
        client.post("/api/v1/records", headers=auth_headers, json={
            "wallet_id": test_wallet.id, "category_id": test_category.id,
            "amount": 200.00, "record_type": "expense", "note": "待删除支出",
            "date": datetime.utcnow().isoformat(),
        })
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == initial_balance - 200.00

        records_resp = client.get("/api/v1/records", headers=auth_headers)
        record_id = records_resp.json()[0]["id"]
        assert client.delete(f"/api/v1/records/{record_id}", headers=auth_headers).status_code == 200
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == initial_balance

    def test_delete_income_record_restores_balance(self, client, auth_headers, test_wallet, test_category):
        initial_balance = 1000.00
        client.post("/api/v1/records", headers=auth_headers, json={
            "wallet_id": test_wallet.id, "category_id": test_category.id,
            "amount": 500.00, "record_type": "income", "note": "待删除收入",
            "date": datetime.utcnow().isoformat(),
        })
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == initial_balance + 500.00

        records_resp = client.get("/api/v1/records", headers=auth_headers)
        record_id = records_resp.json()[0]["id"]
        assert client.delete(f"/api/v1/records/{record_id}", headers=auth_headers).status_code == 200
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == initial_balance


class TestRecordUpdateBalanceAdjustment:
    """更新已确认记录后，钱包余额应正确调整"""

    def test_update_expense_amount_adjusts_balance(self, client, auth_headers, test_wallet, test_category):
        initial_balance = 1000.00
        client.post("/api/v1/records", headers=auth_headers, json={
            "wallet_id": test_wallet.id, "category_id": test_category.id,
            "amount": 200.00, "record_type": "expense", "note": "待修改金额",
            "date": datetime.utcnow().isoformat(),
        })
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == 800.0

        records_resp = client.get("/api/v1/records", headers=auth_headers)
        record_id = records_resp.json()[0]["id"]
        assert client.put(f"/api/v1/records/{record_id}", headers=auth_headers, json={"amount": 300.00}).status_code == 200
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == 700.0

    def test_update_income_amount_adjusts_balance(self, client, auth_headers, test_wallet, test_category):
        initial_balance = 1000.00
        client.post("/api/v1/records", headers=auth_headers, json={
            "wallet_id": test_wallet.id, "category_id": test_category.id,
            "amount": 500.00, "record_type": "income", "note": "待修改收入",
            "date": datetime.utcnow().isoformat(),
        })
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == 1500.0

        records_resp = client.get("/api/v1/records", headers=auth_headers)
        record_id = records_resp.json()[0]["id"]
        assert client.put(f"/api/v1/records/{record_id}", headers=auth_headers, json={"amount": 800.00}).status_code == 200
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == 1800.0

    def test_update_record_type_from_expense_to_income(self, client, auth_headers, test_wallet, test_category):
        initial_balance = 1000.00
        client.post("/api/v1/records", headers=auth_headers, json={
            "wallet_id": test_wallet.id, "category_id": test_category.id,
            "amount": 200.00, "record_type": "expense", "note": "类型切换",
            "date": datetime.utcnow().isoformat(),
        })
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == 800.0

        records_resp = client.get("/api/v1/records", headers=auth_headers)
        record_id = records_resp.json()[0]["id"]
        assert client.put(f"/api/v1/records/{record_id}", headers=auth_headers, json={"record_type": "income"}).status_code == 200
        # 先回滚支出 800→1000，再加收入 1000→1200
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == 1200.0


class TestConfirmRecordBalanceUpdate:
    """确认待确认记录时，钱包余额应正确更新"""

    def test_confirm_pending_expense_updates_balance(self, client, auth_headers, db, test_user, test_wallet):
        from app.models.record import Record, RecordType, RecordStatus
        initial_balance = 1000.00
        record = Record(
            user_id=test_user.id, wallet_id=test_wallet.id, amount=150.00,
            record_type=RecordType.EXPENSE, status=RecordStatus.PENDING,
            note="待确认支出", date=datetime.utcnow(),
        )
        db.add(record); db.commit(); db.refresh(record)
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == initial_balance

        assert client.post(f"/api/v1/records/{record.id}/confirm", headers=auth_headers).status_code == 200
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == initial_balance - 150.00

    def test_confirm_pending_income_updates_balance(self, client, auth_headers, db, test_user, test_wallet):
        from app.models.record import Record, RecordType, RecordStatus
        initial_balance = 1000.00
        record = Record(
            user_id=test_user.id, wallet_id=test_wallet.id, amount=300.00,
            record_type=RecordType.INCOME, status=RecordStatus.PENDING,
            note="待确认收入", date=datetime.utcnow(),
        )
        db.add(record); db.commit(); db.refresh(record)
        assert client.post(f"/api/v1/records/{record.id}/confirm", headers=auth_headers).status_code == 200
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == initial_balance + 300.00


class TestRejectRecordBalanceRollback:
    """拒绝 PENDING 记录 → 余额不应变化"""

    def test_reject_pending_record_does_not_affect_balance(self, client, auth_headers, db, test_user, test_wallet):
        from app.models.record import Record, RecordType, RecordStatus
        initial_balance = 1000.00
        # Create NON-AI PENDING record (is_ai_recognized=0)
        # Non-AI PENDING records do NOT affect balance on creation or rejection
        record = Record(
            user_id=test_user.id, wallet_id=test_wallet.id, amount=100.00,
            record_type=RecordType.EXPENSE, status=RecordStatus.PENDING,
            is_ai_recognized=0, note="手动待拒绝", date=datetime.utcnow(),
        )
        db.add(record); db.commit(); db.refresh(record)
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == initial_balance
        assert client.post(f"/api/v1/records/{record.id}/reject", headers=auth_headers).status_code == 200
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == initial_balance


class TestDeletePendingRecordNoBalanceChange:
    """删除 PENDING 记录不应影响余额"""

    def test_delete_pending_record_no_balance_change(self, client, auth_headers, db, test_user, test_wallet):
        from app.models.record import Record, RecordType, RecordStatus
        initial_balance = 1000.00
        record = Record(
            user_id=test_user.id, wallet_id=test_wallet.id, amount=100.00,
            record_type=RecordType.EXPENSE, status=RecordStatus.PENDING,
            date=datetime.utcnow(),
        )
        db.add(record); db.commit(); db.refresh(record)
        assert client.delete(f"/api/v1/records/{record.id}", headers=auth_headers).status_code == 200
        assert client.get(f"/api/v1/wallets/{test_wallet.id}", headers=auth_headers).json()["balance"] == initial_balance
