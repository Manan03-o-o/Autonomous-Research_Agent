import os
import json
import re
from typing import Optional, Dict, Any, List
from groq import Groq
from app.core.config import settings

_client: Optional[Groq] = None

def get_groq_client() -> Groq:
    global _client
    if _client is None:
        api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured. Please set GROQ_API_KEY in your .env file."
            )
        _client = Groq(api_key=api_key)
    return _client

def get_model_name(override_model: Optional[str] = None) -> str:
    if override_model:
        return override_model
    return settings.GROQ_MODEL or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

def generate_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> str:
    """
    Generate a basic text completion using Groq.
    """
    client = get_groq_client()
    selected_model = get_model_name(model)
    response = client.chat.completions.create(
        messages=messages,
        model=selected_model,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""

def generate_structured_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.0,
    response_format: Dict[str, str] = {"type": "json_object"},
) -> Dict[str, Any]:
    """
    Generate a JSON structured completion using Groq.
    """
    client = get_groq_client()
    selected_model = get_model_name(model)
    
    # Ensure system prompt mentions JSON if not already present
    has_json_instruction = any("json" in m.get("content", "").lower() for m in messages)
    if not has_json_instruction:
        messages = [{"role": "system", "content": "You are a helpful assistant designed to output strictly JSON."}] + list(messages)

    response = client.chat.completions.create(
        messages=messages,
        model=selected_model,
        temperature=temperature,
        response_format=response_format,
    )
    content = response.choices[0].message.content or "{}"
    
    # Clean up potential markdown code fences in case model returns ```json ... ```
    cleaned_content = re.sub(r"^```(?:json)?\s*", "", content.strip())
    cleaned_content = re.sub(r"\s*```$", "", cleaned_content.strip())
    
    return json.loads(cleaned_content)

