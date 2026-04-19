import httpx
import base64
import json
import os
from typing import Optional, Dict, Any
from app.core.config import settings


class AIService:
    """Service for calling Qwen VL API for receipt recognition"""
    
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.api_base = settings.QWEN_API_BASE
        self.model = settings.QWEN_MODEL
    
    async def recognize_receipt(self, image_base64: str) -> Dict[str, Any]:
        """
        Call Qwen VL API to recognize receipt/screenshot.
        Returns extracted data: amount, merchant_name, date, category_guess, confidence
        """
        if not self.api_key:
            # Return mock data for testing without API key
            return self._mock_recognition()
        
        prompt = """你是一个专业的收据识别助手。请分析这张图片中的消费记录，提取以下信息并以JSON格式返回：
        - amount: 消费金额（数字）
        - merchant_name: 商家名称
        - date: 消费日期（格式：YYYY-MM-DD），如果图片中没有则返回null
        - category_guess: 消费分类猜测（如：餐饮、交通、购物、娱乐、医疗、教育、居住、通讯、其他）
        - confidence: 识别置信度（0.0-1.0之间的浮点数）
        
        如果图片中无法识别出有效的消费记录，请返回：
        - amount: null
        - merchant_name: null
        - date: null
        - category_guess: null
        - confidence: 0.0
        - error: "无法识别有效的消费记录"
        
        只返回JSON，不要有其他文字。"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    }
                ]
            }],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                
                # Parse JSON from response
                try:
                    # Try to extract JSON from the content
                    json_str = content
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0]
                    
                    data = json.loads(json_str.strip())
                    return {
                        "amount": data.get("amount"),
                        "merchant_name": data.get("merchant_name"),
                        "date": data.get("date"),
                        "category_guess": data.get("category_guess"),
                        "confidence": data.get("confidence", 0.5),
                        "raw_response": content
                    }
                except json.JSONDecodeError:
                    return {
                        "amount": None,
                        "merchant_name": None,
                        "date": None,
                        "category_guess": None,
                        "confidence": 0.0,
                        "raw_response": content,
                        "error": "JSON解析失败"
                    }
                    
            except httpx.HTTPError as e:
                return {
                    "amount": None,
                    "merchant_name": None,
                    "date": None,
                    "category_guess": None,
                    "confidence": 0.0,
                    "error": f"API调用失败: {str(e)}"
                }
    
    def _mock_recognition(self) -> Dict[str, Any]:
        """Mock recognition result for testing"""
        return {
            "amount": 128.50,
            "merchant_name": "测试商家",
            "date": "2024-01-15",
            "category_guess": "餐饮",
            "confidence": 0.85,
            "raw_response": "Mock response - API key not configured"
        }


ai_service = AIService()
