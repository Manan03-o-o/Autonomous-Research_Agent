import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from google.genai import types
from .planner import get_gemini_client
from app.models.schemas import ClaimResponse

class ClaimExtraction(BaseModel):
    claims: List[str] = Field(description="Factual claims extracted from the text")
    confidence: List[float] = Field(description="Confidence score (0.0 to 1.0) for each claim")

async def extract_claims_from_text(text: str, question: str) -> List[Dict[str, Any]]:
    """
    Extracts relevant factual claims from a piece of text that answer the question.
    """
    if not text:
        return []
        
    client = get_gemini_client()
    
    prompt = f"""
    You are an expert Research Analyst.
    Extract key factual claims from the following text that help answer the research question: "{question}"
    
    Text snippet:
    {text[:4000]} # Limit to 4k characters for safety
    
    Return a list of clear, standalone factual statements and your confidence in their accuracy based solely on the text.
    If the text contains no relevant information, return an empty list.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ClaimExtraction,
            ),
        )
        data = json.loads(response.text)
        
        results = []
        for i, claim in enumerate(data.get("claims", [])):
            conf = data.get("confidence", [])
            confidence = conf[i] if i < len(conf) else 0.8
            results.append({
                "claim": claim,
                "confidence": confidence
            })
        return results
    except Exception as e:
        print(f"Error extracting claims: {e}")
        return []
