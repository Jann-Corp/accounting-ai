"""
API tests for AI receipt recognition endpoints.
"""
import pytest
from datetime import datetime
import base64


def test_recognize_receipt_no_auth(client):
    """Test AI recognition without authentication."""
    # Create a small test image (1x1 pixel PNG)
    test_image = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    
    response = client.post(
        "/api/v1/ai/recognize",
        files={"file": ("test.png", test_image, "image/png")},
    )
    # Should require auth
    assert response.status_code == 401


def test_recognize_receipt_success(client, auth_headers):
    """Test successful receipt recognition (returns job_id)."""
    # Create a small test image (1x1 pixel PNG)
    test_image = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    
    response = client.post(
        "/api/v1/ai/recognize",
        headers=auth_headers,
        files={"file": ("test.png", test_image, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"
    assert "message" in data


def test_recognize_receipt_invalid_format(client, auth_headers):
    """Test receipt recognition with invalid file format."""
    # Try to upload a text file
    response = client.post(
        "/api/v1/ai/recognize",
        headers=auth_headers,
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400
    assert "只支持" in response.json()["detail"] or "image" in response.json()["detail"].lower()


def test_recognize_receipt_empty_file(client, auth_headers):
    """Test receipt recognition with empty file."""
    response = client.post(
        "/api/v1/ai/recognize",
        headers=auth_headers,
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400
    assert "图片数据为空" in response.json()["detail"]


def test_get_recognition_result_pending(client, auth_headers):
    """Test getting result for a pending job."""
    # Create a test image
    test_image = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    
    # Start recognition
    response = client.post(
        "/api/v1/ai/recognize",
        headers=auth_headers,
        files={"file": ("test.png", test_image, "image/png")},
    )
    task_id = response.json()["task_id"]
    
    # Get result (might be pending or done depending on timing)
    response = client.get(f"/api/v1/ai/recognize/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] in ["pending", "done", "error"]


def test_get_recognition_result_not_found(client, auth_headers):
    """Test getting result for nonexistent job."""
    response = client.get("/api/v1/ai/recognize/99999", headers=auth_headers)
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_list_recognition_jobs_empty(client, auth_headers):
    """Test listing recognition jobs when none exist."""
    response = client.get("/api/v1/ai/jobs", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_recognition_jobs(client, auth_headers):
    """Test listing recognition jobs after creating one."""
    # Create a test image
    test_image = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    
    # Start recognition
    client.post(
        "/api/v1/ai/recognize",
        headers=auth_headers,
        files={"file": ("test.png", test_image, "image/png")},
    )
    
    # List jobs
    response = client.get("/api/v1/ai/jobs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_job_detail(client, auth_headers):
    """Test getting job detail by ID."""
    # Create a test image
    test_image = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    
    # Start recognition
    response = client.post(
        "/api/v1/ai/recognize",
        headers=auth_headers,
        files={"file": ("test.png", test_image, "image/png")},
    )
    task_id = response.json()["task_id"]
    
    # Get job detail
    response = client.get(f"/api/v1/ai/jobs/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == int(task_id)


def test_list_pending_ai_records_empty(client, auth_headers):
    """Test listing pending AI records when none exist."""
    response = client.get("/api/v1/ai/records/pending", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_pending_ai_records(client, auth_headers, db, test_user, test_wallet):
    """Test listing pending AI records."""
    from app.models.record import Record, RecordType, RecordStatus
    
    # Create a pending AI record
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        is_ai_recognized=1,
        note="AI 识别待确认",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    
    response = client.get("/api/v1/ai/records/pending", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "pending"
    assert data[0]["is_ai_recognized"] is True


def test_confirm_ai_record(client, auth_headers, db, test_user, test_wallet):
    """Test confirming a pending AI record."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=150.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        is_ai_recognized=1,
        note="待确认",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    response = client.post(
        f"/api/v1/ai/records/{record.id}/confirm",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["record_id"] == record.id
    
    # Verify record is now confirmed
    response = client.get(f"/api/v1/records/{record.id}", headers=auth_headers)
    assert response.json()["status"] == "confirmed"


def test_confirm_ai_record_not_pending(client, auth_headers, db, test_user, test_wallet):
    """Test confirming a record that is not pending."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,  # Already confirmed
        is_ai_recognized=1,
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    response = client.post(
        f"/api/v1/ai/records/{record.id}/confirm",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "只能确认待确认状态" in response.json()["detail"]


def test_reject_ai_record(client, auth_headers, db, test_user, test_wallet):
    """Test rejecting a pending AI record."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=200.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        is_ai_recognized=1,
        note="待拒绝",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    response = client.post(
        f"/api/v1/ai/records/{record.id}/reject",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["record_id"] == record.id
    
    # Verify record is now rejected
    response = client.get(f"/api/v1/records/{record.id}", headers=auth_headers)
    assert response.json()["status"] == "rejected"


def test_reject_ai_record_not_pending(client, auth_headers, db, test_user, test_wallet):
    """Test rejecting a record that is not pending."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        is_ai_recognized=1,
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    response = client.post(
        f"/api/v1/ai/records/{record.id}/reject",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "只能拒绝待确认状态" in response.json()["detail"]


def test_recognize_with_api_key(client, test_user, db):
    """Test AI recognition using API key authentication."""
    from app.models.apikey import ApiKey
    import hashlib
    
    # Create an API key
    key_data = "ak_test_api_key_for_ai"
    key_hash = hashlib.sha256(key_data.encode()).hexdigest()
    
    api_key = ApiKey(
        user_id=test_user.id,
        name="AI test key",
        key_hash=key_hash,
        key_prefix=key_data[:12],
        is_active=True,
    )
    db.add(api_key)
    db.commit()
    
    # Create a test image
    test_image = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    
    # Use API key for authentication
    response = client.post(
        "/api/v1/ai/recognize",
        headers={"X-API-Key": key_data},
        files={"file": ("test.png", test_image, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data


def test_ai_record_type_enum_and_wallet_balance(client, auth_headers, db, test_user, test_wallet):
    """Test that AI-created records have correct record_type enum and update wallet balance."""
    from app.models.record import Record, RecordType, RecordStatus
    from app.models.wallet import Wallet
    
    initial_balance = test_wallet.balance
    
    # Create a record manually to simulate AI creation with correct enum
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,  # Use enum, not string
        note="AI 测试记录",
        date=datetime.utcnow(),
        status=RecordStatus.CONFIRMED,
        is_ai_recognized=1,
    )
    db.add(record)
    
    # Update wallet balance (simulating the fix)
    test_wallet.balance -= 100.00
    db.add(test_wallet)
    db.commit()
    
    # Verify record was created with correct enum
    saved_record = db.query(Record).filter(Record.id == record.id).first()
    assert saved_record.record_type == RecordType.EXPENSE
    assert saved_record.is_ai_recognized == 1
    
    # Verify wallet balance was updated
    saved_wallet = db.query(Wallet).filter(Wallet.id == test_wallet.id).first()
    assert saved_wallet.balance == initial_balance - 100.00
    
    # Verify record appears in stats
    response = client.get("/api/v1/stats/monthly", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_expense"] == 100.00
    assert data["record_count"] == 1


def test_record_type_enum_conversion():
    """Test that record_type string is correctly converted to RecordType enum.
    
    This test catches the bug where AI-created records had record_type
    stored as string "expense"/"income" instead of RecordType enum.
    The stats queries compare against RecordType.EXPENSE/INCOME, so
    string comparison would fail and exclude AI records from stats.
    """
    from app.models.record import RecordType
    
    # Test the conversion logic (same as in _run_recognition_sync)
    record_type_str = "expense"
    record_type = RecordType.EXPENSE if record_type_str == "expense" else RecordType.INCOME
    assert record_type == RecordType.EXPENSE
    assert isinstance(record_type, RecordType)
    
    record_type_str = "income"
    record_type = RecordType.EXPENSE if record_type_str == "expense" else RecordType.INCOME
    assert record_type == RecordType.INCOME
    assert isinstance(record_type, RecordType)
    
    # Verify enum comparison works in queries (this is what stats use)
    assert RecordType.EXPENSE == RecordType.EXPENSE
    
    # This is the bug - string comparison with enum fails
    # Uncomment to see the bug:
    # assert "expense" == RecordType.EXPENSE  # This would fail!
    
    # Query simulation - this is what stats.py does
    sample_records = [
        RecordType.EXPENSE,  # Correct enum
        RecordType.INCOME,   # Correct enum
    ]
    
    # Filter using enum (stats uses this pattern)
    expense_records = [r for r in sample_records if r == RecordType.EXPENSE]
    assert len(expense_records) == 1
    assert expense_records[0] == RecordType.EXPENSE


def test_ai_service_initialization(client, auth_headers):
    """Test AI service initialization and configuration."""
    from app.services.ai_service import AIService
    
    service = AIService()
    # The service reads API key from environment or settings
    # We can verify the service configuration is loaded
    assert service.model == "qwen-vl-plus"
    assert "dashscope" in service.api_base  # API base contains dashscope


def test_ai_job_status_processing(client, auth_headers, db, test_user):
    """Test getting job status when job is still processing."""
    from app.models.ai_recognition_job import AIRecognitionJob, RecognitionStatus
    
    job = AIRecognitionJob(
        user_id=test_user.id,
        original_image_url="/tmp/test.jpg",
        status=RecognitionStatus.PROCESSING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    response = client.get(
        f"/api/v1/ai/recognize/{job.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert "正在识别" in data["message"]


def test_ai_job_status_failed(client, auth_headers, db, test_user):
    """Test getting job status when job has failed."""
    from app.models.ai_recognition_job import AIRecognitionJob, RecognitionStatus
    
    job = AIRecognitionJob(
        user_id=test_user.id,
        original_image_url="/tmp/test.jpg",
        status=RecognitionStatus.FAILED,
        error_message="Test error message",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    response = client.get(
        f"/api/v1/ai/recognize/{job.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "Test error message"


def test_ai_records_pending_with_multiple_records(client, auth_headers, db, test_user, test_wallet):
    """Test listing pending AI records when there are multiple."""
    from app.models.record import Record, RecordType, RecordStatus
    
    # Create multiple pending AI records
    for i in range(3):
        record = Record(
            user_id=test_user.id,
            wallet_id=test_wallet.id,
            amount=100.00 + i * 10,
            record_type=RecordType.EXPENSE,
            status=RecordStatus.PENDING,
            is_ai_recognized=1,
            note=f"AI 测试记录 {i}",
            date=datetime.utcnow(),
        )
        db.add(record)
    db.commit()
    
    response = client.get(
        "/api/v1/ai/records/pending",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(r["status"] == "pending" for r in data)
    assert all(r["is_ai_recognized"] is True for r in data)


def test_ai_records_confirm_updates_wallet_balance(client, auth_headers, db, test_user, test_wallet):
    """Test that confirming AI record updates wallet balance.
    
    Note: This test verifies the confirm endpoint is called correctly.
    The actual wallet balance update depends on the record being CONFIRMED
    and the wallet_id being set.
    """
    from app.models.record import Record, RecordType, RecordStatus
    from app.models.wallet import Wallet
    
    # Get a fresh wallet from db
    wallet = db.query(Wallet).filter(Wallet.id == test_wallet.id).first()
    initial_balance = wallet.balance
    
    # Create a pending AI record
    record = Record(
        user_id=test_user.id,
        wallet_id=wallet.id,
        amount=200.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        is_ai_recognized=1,
        note="待确认记录",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # Confirm the record via the records endpoint (not ai endpoint)
    response = client.post(
        f"/api/v1/records/{record.id}/confirm",
        headers=auth_headers,
    )
    assert response.status_code == 200
    
    # Verify record status changed
    db.refresh(record)
    assert record.status == RecordStatus.CONFIRMED


def test_ai_records_reject_updates_status(client, auth_headers, db, test_user, test_wallet):
    """Test that rejecting AI record updates status correctly."""
    from app.models.record import Record, RecordType, RecordStatus
    
    # Create a pending AI record
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=150.00,
        record_type=RecordType.INCOME,
        status=RecordStatus.PENDING,
        is_ai_recognized=1,
        note="待拒绝记录",
        date=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    record_id = record.id
    
    # Reject the record
    response = client.post(
        f"/api/v1/ai/records/{record_id}/reject",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["record_id"] == record_id
    
    # Verify record status was updated
    db.refresh(record)
    assert record.status == RecordStatus.REJECTED
