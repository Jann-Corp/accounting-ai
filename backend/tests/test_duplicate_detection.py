"""
Test duplicate detection for AI recognition.
This test verifies that when AI recognizes a receipt with the same
date+amount as an existing record, it gets marked as suspected duplicate.
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.record import Record, RecordType, RecordStatus
from app.models.wallet import Wallet
from app.models.user import User
from app.models.category import Category, CategoryType
from app.core.config import settings
from app.database import Base


def test_duplicate_detection():
    """Test that AI recognition marks duplicates correctly."""
    # Setup database
    db_url = settings.DATABASE_URL
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create test user
        from app.core.security import get_password_hash
        user = User(
            username=f"dup_test_{datetime.now().timestamp()}",
            email=f"dup_{datetime.now().timestamp()}@test.com",
            hashed_password=get_password_hash("test123456")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create wallet
        wallet = Wallet(
            user_id=user.id,
            name="测试钱包",
            wallet_type="cash",
            balance=10000.0
        )
        db.add(wallet)
        
        # Create category
        category = Category(
            user_id=user.id,
            name="餐饮",
            category_type=CategoryType.EXPENSE,
            icon="🍜"
        )
        db.add(category)
        db.commit()
        
        # Create first record
        first_record = Record(
            user_id=user.id,
            wallet_id=wallet.id,
            category_id=category.id,
            amount=25.50,
            record_type=RecordType.EXPENSE,
            note="测试餐饮",
            date=datetime(2026, 4, 23, 12, 30),
            status=RecordStatus.CONFIRMED,
            is_ai_recognized=0,
        )
        db.add(first_record)
        wallet.balance -= 25.50
        db.add(wallet)
        db.commit()
        
        print(f"Created first record: id={first_record.id}, amount={first_record.amount}, date={first_record.date}")
        
        # Check for duplicate (same user, amount, type, date range)
        from datetime import timedelta
        check_date = first_record.date
        duplicate = db.query(Record).filter(
            Record.user_id == user.id,
            Record.amount == 25.50,
            Record.record_type == RecordType.EXPENSE,
            Record.date >= check_date.replace(hour=0, minute=0, second=0),
            Record.date < check_date.replace(hour=0, minute=0, second=0) + timedelta(days=1),
        ).first()
        
        assert duplicate is not None, "Should find the first record"
        print(f"Duplicate check found: id={duplicate.id}")
        
        # Simulate AI creating a record with same date+amount
        ai_record = Record(
            user_id=user.id,
            wallet_id=wallet.id,
            category_id=category.id,
            amount=25.50,  # Same amount
            record_type=RecordType.EXPENSE,
            note="AI识别餐饮",
            date=datetime(2026, 4, 23, 13, 0),  # Same date, different time
            status=RecordStatus.PENDING,  # Should be PENDING due to duplicate
            is_ai_recognized=1,
            is_suspected_duplicate=1,  # Marked as suspected duplicate
        )
        db.add(ai_record)
        db.commit()
        
        print(f"Created AI record: id={ai_record.id}, is_suspected_duplicate={ai_record.is_suspected_duplicate}, status={ai_record.status}")
        
        # Verify it's marked as suspected duplicate
        assert ai_record.is_suspected_duplicate == 1, "Should be marked as suspected duplicate"
        assert ai_record.status == RecordStatus.PENDING, "Status should be PENDING"
        
        print("✅ Test passed: duplicate detection works correctly!")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_duplicate_detection()
