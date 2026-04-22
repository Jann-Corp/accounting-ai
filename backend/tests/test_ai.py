"""
API tests for AI recognition endpoints.
"""
import pytest
import base64
from datetime import datetime


def test_recognize_receipt_success(client, auth_headers, test_wallet, db, test_user):
    """Test successful receipt recognition (uses mock data when no API key)."""
    # Create a simple test image (1x1 pixel PNG)
    test_image = base64.b64encode(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82').decode('utf-8')
    
    response = client.post(
        "/api/v1/ai/recognize",
        headers=auth_headers,
        files={"file": ("test.png", base64.b64decode(test_image), "image/png")},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"
    assert "正在识别" in data["message"]


def test_recognize_receipt_no_auth(client):
    """Test receipt recognition without authentication."""
    test_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82'
    
    response = client.post(
        "/api/v1/ai/recognize",
        files={"file": ("test.png", test_image, "image/png")},
    )
    
    assert response.status_code == 401


def test_recognize_receipt_invalid_format(client, auth_headers):
    """Test receipt recognition with invalid file format."""
    response = client.post(
        "/api/v1/ai/recognize",
        headers=auth_headers,
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )
    
    assert response.status_code == 400
    assert "只支持" in response.json()["detail"]


def test_get_recognition_result_not_found(client, auth_headers):
    """Test getting result for nonexistent job."""
    response = client.get("/api/v1/ai/recognize/99999", headers=auth_headers)
    assert response.status_code == 404


def test_list_recognition_jobs(client, auth_headers, db, test_user):
    """Test listing recognition jobs."""
    from app.models.ai_recognition_job import AIRecognitionJob, RecognitionStatus
    
    job = AIRecognitionJob(
        user_id=test_user.id,
        original_image_url="/path/to/image.png",
        status=RecognitionStatus.DONE,
        result_json='{"records": []}',
    )
    db.add(job)
    db.commit()
    
    response = client.get("/api/v1/ai/jobs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_recognition_job_detail(client, auth_headers, db, test_user):
    """Test getting job detail."""
    from app.models.ai_recognition_job import AIRecognitionJob, RecognitionStatus
    
    job = AIRecognitionJob(
        user_id=test_user.id,
        original_image_url="/path/to/image.png",
        status=RecognitionStatus.DONE,
        result_json='{"records": []}',
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    response = client.get(f"/api/v1/ai/jobs/{job.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job.id


def test_get_recognition_job_detail_unauthorized(client, auth_headers, db, test_user):
    """Test getting job detail for another user's job."""
    from app.models.ai_recognition_job import AIRecognitionJob, RecognitionStatus
    from app.models.user import User
    from app.core.security import get_password_hash
    
    # Create another user
    other_user = User(
        username="otheruser",
        email="other@example.com",
        hashed_password=get_password_hash("password"),
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    
    # Create job for other user
    job = AIRecognitionJob(
        user_id=other_user.id,
        original_image_url="/path/to/image.png",
        status=RecognitionStatus.DONE,
    )
    db.add(job)
    db.commit()
    
    response = client.get(f"/api/v1/ai/jobs/{job.id}", headers=auth_headers)
    assert response.status_code == 404


def test_list_pending_ai_records(client, auth_headers, db, test_user, test_wallet):
    """Test listing pending AI records."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        note="AI 识别待确认",
        date=datetime.utcnow(),
        is_ai_recognized=1,
    )
    db.add(record)
    db.commit()
    
    response = client.get("/api/v1/ai/records/pending", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "pending"


def test_confirm_ai_record(client, auth_headers, db, test_user, test_wallet):
    """Test confirming a pending AI record."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        note="待确认",
        date=datetime.utcnow(),
        is_ai_recognized=1,
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
    
    # Verify status changed in DB
    db.refresh(record)
    assert record.status == RecordStatus.CONFIRMED


def test_reject_ai_record(client, auth_headers, db, test_user, test_wallet):
    """Test rejecting a pending AI record."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.PENDING,
        note="待确认",
        date=datetime.utcnow(),
        is_ai_recognized=1,
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
    
    # Verify status changed in DB
    db.refresh(record)
    assert record.status == RecordStatus.REJECTED


def test_confirm_nonexistent_record(client, auth_headers):
    """Test confirming nonexistent record."""
    response = client.post(
        "/api/v1/ai/records/99999/confirm",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_confirm_already_confirmed_record(client, auth_headers, db, test_user, test_wallet):
    """Test confirming a record that's already confirmed."""
    from app.models.record import Record, RecordType, RecordStatus
    
    record = Record(
        user_id=test_user.id,
        wallet_id=test_wallet.id,
        amount=100.00,
        record_type=RecordType.EXPENSE,
        status=RecordStatus.CONFIRMED,
        note="已确认",
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
    assert "not pending" in response.json()["detail"]


def test_recognition_job_status_flow(client, auth_headers, db, test_user):
    """Test the full flow of recognition job status."""
    from app.models.ai_recognition_job import AIRecognitionJob, RecognitionStatus
    
    # Create a pending job
    job = AIRecognitionJob(
        user_id=test_user.id,
        original_image_url="/path/to/image.png",
        status=RecognitionStatus.PENDING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    response = client.get(f"/api/v1/ai/recognize/{job.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert "排队" in response.json()["message"]
    
    # Update to processing
    job.status = RecognitionStatus.PROCESSING
    db.commit()
    
    response = client.get(f"/api/v1/ai/recognize/{job.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert "正在识别" in response.json()["message"]
    
    # Update to failed
    job.status = RecognitionStatus.FAILED
    job.error_message = "测试错误"
    db.commit()
    
    response = client.get(f"/api/v1/ai/recognize/{job.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert "测试错误" in response.json()["message"]
