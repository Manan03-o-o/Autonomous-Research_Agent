import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services.llm_service import generate_structured_completion

class ClaimExtraction(BaseModel):
    claims: List[str] = Field(description="Factual claims extracted from the text")
    confidence: List[float] = Field(description="Confidence score (0.0 to 1.0) for each claim")

async def extract_claims_from_text(text: str, question: str) -> List[Dict[str, Any]]:
    """
    Extracts relevant factual claims from a piece of text that answer the question using Groq.
    """
    if not text:
        return []
        
    prompt = f"""
    You are an expert Research Analyst.
    Extract key factual claims from the following text that help answer the research question: "{question}"
    
    Text snippet:
    {text[:4000]} # Limit to 4k characters for safety
    
    Return a list of clear, standalone factual statements and your confidence in their accuracy based solely on the text.
    If the text contains no relevant information, return an empty list.
    
    Return strictly JSON matching this structure:
    {{
      "claims": ["claim 1", "claim 2"],
      "confidence": [0.95, 0.8]
    }}
    """
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant designed to output strictly JSON."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        data = generate_structured_completion(messages=messages)
        
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
