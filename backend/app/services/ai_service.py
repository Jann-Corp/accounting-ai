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
    
    async def recognize_receipt(self, image_base64: str) -> list:
        """
        Call Qwen VL API to recognize receipt/screenshot.
        Returns extracted data: amount, merchant_name, date, category_guess, confidence
        """
        if not self.api_key:
            # Return mock data for testing without API key
            return self._mock_recognition()
        
        prompt = settings.AI_RECOGNITION_PROMPT
        
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
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Parse JSON from response
                try:
                    json_str = content
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0]

                    data = json.loads(json_str.strip())

                    # Support both single object and array responses
                    if isinstance(data, list):
                        records = data
                    elif isinstance(data, dict):
                        records = [data]
                    else:
                        records = []

                    return [
                        {
                            "amount": r.get("amount"),
                            "merchant_name": r.get("merchant_name"),
                            "date": r.get("date"),
                            "category_guess": r.get("category_guess"),
                            "confidence": r.get("confidence", 0.5),
                            "raw_response": json.dumps(r, ensure_ascii=False)
                        }
                        for r in records
                        if isinstance(r, dict)
                    ] if records else [{
                        "amount": None,
                        "merchant_name": None,
                        "date": None,
                        "category_guess": None,
                        "confidence": 0.0,
                        "raw_response": content,
                    }]

                except json.JSONDecodeError:
                    print(f"DEBUG JSON PARSE ERROR, content: {content[:200]}")
                    return [{
                        "amount": None,
                        "merchant_name": None,
                        "date": None,
                        "category_guess": None,
                        "confidence": 0.0,
                        "raw_response": content,
                    }]
                    
            except httpx.HTTPError as e:
                print("DEBUG AI API ERROR:", e, "response:", getattr(response, "text", "N/A"))
                return [{
                    "amount": None,
                    "merchant_name": None,
                    "date": None,
                    "category_guess": None,
                    "confidence": 0.0,
                    "raw_response": f"API调用失败: {str(e)}"
                }]

    def _mock_recognition(self) -> list:
        """Mock recognition result for testing"""
        return [{
            "amount": 128.50,
            "merchant_name": "测试商家",
            "date": "2024-01-15",
            "category_guess": "餐饮",
            "confidence": 0.85,
            "raw_response": "Mock response - API key not configured"
        }]


ai_service = AIService()
