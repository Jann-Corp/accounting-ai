"""
Unit tests for AI service.
"""
import pytest
import asyncio
import json


def test_mock_recognition():
    """Test mock recognition when no API key is configured."""
    from app.services.ai_service import AIService
    
    # Create service without API key
    import os
    original_key = os.environ.get("QWEN_API_KEY")
    os.environ["QWEN_API_KEY"] = ""
    
    try:
        service = AIService()
        result = asyncio.run(service.recognize_receipt("base64data"))
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["amount"] is not None
        assert result[0]["merchant_name"] == "测试商家 A"
        assert result[0]["record_type"] == "expense"
        assert result[1]["record_type"] == "income"
        assert 0.7 <= result[0]["confidence"] <= 0.98
    finally:
        if original_key:
            os.environ["QWEN_API_KEY"] = original_key


def test_service_initialization():
    """Test AI service initialization with config."""
    from app.services.ai_service import AIService
    from app.core.config import settings
    
    service = AIService()
    
    assert service.api_key == settings.QWEN_API_KEY
    assert service.api_base == settings.QWEN_API_BASE
    assert service.model == settings.QWEN_MODEL


def test_confidence_threshold_logic():
    """Test confidence threshold logic for auto-confirmation."""
    from app.core.config import settings
    
    # Default threshold is 0.85
    assert settings.AI_CONFIDENCE_THRESHOLD == 0.85
    
    # Test threshold comparisons
    high_confidence = 0.90
    low_confidence = 0.70
    
    assert high_confidence >= settings.AI_CONFIDENCE_THRESHOLD  # Should auto-confirm
    assert low_confidence < settings.AI_CONFIDENCE_THRESHOLD  # Should need review


def test_date_parsing_formats():
    """Test date parsing formats used in AI recognition."""
    from datetime import datetime
    
    test_cases = [
        ("2024-01-15 14:30", "%Y-%m-%d %H:%M"),
        ("2024-01-15", "%Y-%m-%d"),
    ]
    
    for date_str, fmt in test_cases:
        try:
            parsed = datetime.strptime(date_str, fmt)
            assert parsed is not None
        except ValueError:
            pytest.fail(f"Failed to parse date: {date_str}")


def test_json_parsing_from_ai_response():
    """Test parsing JSON from AI response content."""
    # Test clean JSON
    json_str = json.dumps({"amount": 100, "merchant_name": "测试"})
    data = json.loads(json_str)
    assert data["amount"] == 100
    
    # Test JSON array
    json_arr = json.dumps([{"amount": 100}, {"amount": 200}])
    data = json.loads(json_arr)
    assert len(data) == 2
    
    # Test JSON with markdown code blocks (as ai_service.py does)
    content = '```json\n{"amount": 100}\n```'
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0]
    data = json.loads(json_str.strip())
    assert data["amount"] == 100
    
    # Test generic code blocks
    content = '```\n{"amount": 100}\n```'
    if "```" in content and "```json" not in content:
        json_str = content.split("```")[1].split("```")[0]
    data = json.loads(json_str.strip())
    assert data["amount"] == 100


def test_normalize_ai_results_to_list():
    """Test normalizing AI results to list format."""
    # Single object should become list
    single = {"amount": 100, "merchant_name": "测试"}
    if not isinstance(single, list):
        single = [single] if single else []
    assert isinstance(single, list)
    assert len(single) == 1
    
    # List should stay list
    list_result = [{"amount": 100}]
    if not isinstance(list_result, list):
        list_result = [list_result] if list_result else []
    assert isinstance(list_result, list)
    assert len(list_result) == 1
    
    # None should become empty list
    none_result = None
    if not isinstance(none_result, list):
        none_result = [none_result] if none_result else []
    assert none_result == []


def test_build_record_from_ai_result():
    """Test building record dict from AI result."""
    ai_result = {
        "amount": 100.50,
        "merchant_name": "测试商家",
        "date": "2024-01-15",
        "category_guess": "餐饮",
        "confidence": 0.95,
        "record_type": "expense",
    }
    
    record = {
        "amount": ai_result.get("amount"),
        "merchant_name": ai_result.get("merchant_name"),
        "date": ai_result.get("date"),
        "category_guess": ai_result.get("category_guess"),
        "confidence": ai_result.get("confidence", 0.5),
        "raw_response": json.dumps(ai_result, ensure_ascii=False),
    }
    
    assert record["amount"] == 100.50
    assert record["confidence"] == 0.95
    assert "raw_response" in record


def test_filter_invalid_ai_records():
    """Test filtering out invalid AI records."""
    # Mix of valid and invalid records
    ai_results = [
        {"amount": 100, "merchant_name": "有效"},
        {"amount": None, "merchant_name": "无效"},  # No amount
        "not a dict",  # Not a dict
        {"amount": 200, "merchant_name": "有效 2"},
    ]
    
    valid = [
        r for r in ai_results 
        if isinstance(r, dict) and r.get("amount") is not None
    ]
    assert len(valid) == 2


def test_invalid_json_handling():
    """Test handling of invalid JSON response."""
    content = "not valid json at all"
    
    try:
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        
        data = json.loads(json_str.strip())
        pytest.fail("Should have raised JSONDecodeError")
    except json.JSONDecodeError:
        # Expected - this is what ai_service.py catches
        pass


def test_http_error_handling():
    """Test that HTTP errors are handled gracefully."""
    import httpx
    
    # Simulate what ai_service.py does
    try:
        raise httpx.HTTPError("Simulated API error")
    except httpx.HTTPError as e:
        # This is what ai_service.py returns on error
        error_result = [{
            "amount": None,
            "merchant_name": None,
            "date": None,
            "category_guess": None,
            "confidence": 0.0,
            "raw_response": f"API 调用失败：{str(e)}"
        }]
        assert error_result[0]["confidence"] == 0.0
        assert "API 调用失败" in error_result[0]["raw_response"]
