from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.category import Category, CategoryType
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserUpdate
from app.schemas.category import CategoryResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create default categories for new user
    default_expense_categories = [
        ("餐饮", "🍜"), ("交通", "🚗"), ("购物", "🛒"), ("娱乐", "🎮"),
        ("医疗", "💊"), ("教育", "📚"), ("居住", "🏠"), ("通讯", "📱"), ("其他", "📦")
    ]
    default_income_categories = [
        ("工资", "💰"), ("兼职", "💼"), ("投资", "📈"), ("礼金", "🎁"), ("退款", "💸"), ("其他", "💵")
    ]
    
    for name, icon in default_expense_categories:
        cat = Category(user_id=user.id, name=name, category_type=CategoryType.EXPENSE, icon=icon, is_default=True)
        db.add(cat)
    
    for name, icon in default_income_categories:
        cat = Category(user_id=user.id, name=name, category_type=CategoryType.INCOME, icon=icon, is_default=True)
        db.add(cat)
    
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user settings (e.g., default_wallet_id)"""
    if user_data.default_wallet_id is not None:
        current_user.default_wallet_id = user_data.default_wallet_id
        db.commit()
        db.refresh(current_user)
    return current_user
