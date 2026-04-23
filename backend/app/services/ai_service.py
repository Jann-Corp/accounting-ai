import httpx
import base64
import json
import os
from typing import Optional, Dict, Any, Literal
from app.core.config import settings


class AIService:
    """Service for calling AI vision APIs for receipt recognition.
    
    Supports multiple AI providers:
    - Qwen (Alibaba)
    - Minimax
    """
    
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.AI_PROVIDER
    
    async def recognize_receipt(self, image_base64: str) -> list:
        """Call AI vision API to recognize receipt/screenshot."""
        if self.provider == "minimax":
            return await self._recognize_minimax(image_base64)
        else:
            return await self._recognize_qwen(image_base64)
    
    def _get_prompt(self) -> str:
        """Get the AI recognition prompt."""
        from datetime import datetime
        tz_offset = os.environ.get("TZ", "Asia/Shanghai")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        return f"[系统当前日期时间: {current_time}]\n\n" + settings.AI_RECOGNITION_PROMPT
    
    async def _recognize_qwen(self, image_base64: str) -> list:
        """Call Qwen VL API for receipt recognition."""
        api_key = settings.QWEN_API_KEY
        api_base = settings.QWEN_API_BASE
        model = settings.QWEN_MODEL
        
        if not api_key:
            return self._mock_recognition()
        
        prompt = self._get_prompt()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
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
                    f"{api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return self._parse_response(content)

            except httpx.HTTPError as e:
                print("DEBUG AI API ERROR:", e, "response:", getattr(response, "text", "N/A"))
                return self._error_response(f"API调用失败: {str(e)}")
    
    async def _recognize_minimax(self, image_base64: str) -> list:
        """Call Minimax VL API for receipt recognition."""
        api_key = settings.MINIMAX_API_KEY
        api_base = settings.MINIMAX_API_BASE
        model = settings.MINIMAX_MODEL
        
        if not api_key:
            return self._mock_recognition()
        
        prompt = self._get_prompt()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
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
        
        # Minimax chat completions API
        url = f"{api_base}/chat/completions"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return self._parse_response(content)

            except httpx.HTTPError as e:
                print("DEBUG MINIMAX API ERROR:", e, "response:", getattr(response, "text", "N/A"))
                return self._error_response(f"Minimax API调用失败: {str(e)}")
    
    def _parse_response(self, content: str) -> list:
        """Parse JSON from AI response content."""
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
                    "record_type": r.get("record_type"),
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
                "record_type": None,
                "merchant_name": None,
                "date": None,
                "category_guess": None,
                "confidence": 0.0,
                "raw_response": content,
            }]

        except json.JSONDecodeError:
            print(f"DEBUG JSON PARSE ERROR, content: {content[:200]}")
            return self._error_response(f"JSON解析失败: {content[:200]}")
    
    def _error_response(self, error_msg: str) -> list:
        """Return error response."""
        return [{
            "amount": None,
            "record_type": None,
            "merchant_name": None,
            "date": None,
            "category_guess": None,
            "confidence": 0.0,
            "raw_response": error_msg
        }]
    
    def _mock_recognition(self) -> list:
        """Mock recognition result for testing."""
        import random
        return [
            {
                "amount": round(random.uniform(10, 200), 2),
                "merchant_name": "测试商家 A",
                "date": "2024-01-15",
                "category_guess": "餐饮",
                "confidence": round(random.uniform(0.7, 0.98), 2),
                "record_type": "expense",
                "raw_response": "Mock response - API key not configured",
            },
            {
                "amount": round(random.uniform(100, 3000), 2),
                "merchant_name": "工资入账",
                "date": "2024-01-15 09:00",
                "category_guess": "工资",
                "confidence": round(random.uniform(0.7, 0.98), 2),
                "record_type": "income",
                "raw_response": "Mock response - API key not configured",
            },
        ]


ai_service = AIService()
