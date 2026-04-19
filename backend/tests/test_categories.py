"""
API tests for category endpoints.
"""
import pytest


def test_list_categories(client, auth_headers, test_category):
    """Test listing categories."""
    response = client.get("/api/v1/categories", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(c["name"] == "餐饮" for c in data)


def test_list_categories_filter_by_type(client, auth_headers, test_category):
    """Test listing categories filtered by type."""
    response = client.get(
        "/api/v1/categories?category_type=expense",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    for cat in data:
        assert cat["category_type"] == "expense"


def test_create_category(client, auth_headers):
    """Test creating a category."""
    response = client.post(
        "/api/v1/categories",
        headers=auth_headers,
        json={
            "name": "娱乐",
            "category_type": "expense",
            "icon": "🎮",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "娱乐"
    assert data["icon"] == "🎮"


def test_update_category(client, auth_headers, test_category):
    """Test updating a category."""
    response = client.put(
        f"/api/v1/categories/{test_category.id}",
        headers=auth_headers,
        json={"name": "餐饮更新", "icon": "🍽️"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "餐饮更新"
    assert data["icon"] == "🍽️"


def test_delete_category(client, auth_headers, test_category):
    """Test deleting a category."""
    response = client.delete(
        f"/api/v1/categories/{test_category.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    
    # Verify it's deleted
    response = client.get(
        f"/api/v1/categories/{test_category.id}",
        headers=auth_headers,
    )
    # Actually the API returns 200 for list, let me check detail
    cats = client.get("/api/v1/categories", headers=auth_headers).json()
    assert test_category.id not in [c["id"] for c in cats]


def test_cannot_delete_default_category(client, auth_headers, db, test_user):
    """Test that default categories cannot be deleted."""
    # Create a default category
    from app.models.category import Category, CategoryType
    default_cat = Category(
        user_id=test_user.id,
        name="默认分类",
        category_type=CategoryType.EXPENSE,
        icon="📦",
        is_default=True,
    )
    db.add(default_cat)
    db.commit()
    db.refresh(default_cat)
    
    response = client.delete(
        f"/api/v1/categories/{default_cat.id}",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "默认分类不能删除" in response.json()["detail"]
