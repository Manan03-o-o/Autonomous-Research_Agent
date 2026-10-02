import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services.llm_service import generate_structured_completion

class CriticEvaluation(BaseModel):
    is_sufficient: bool = Field(description="True if the gathered evidence is sufficient to answer the research question")
    missing_information: str = Field(description="What critical information is missing, if any")
    contradictions: List[str] = Field(description="List of conflicting claims found in the evidence")
    additional_queries: List[str] = Field(description="New search queries to run if evidence is insufficient")

async def evaluate_research(question: str, plan: Dict[str, Any], claims_and_evidence: List[Dict[str, Any]]) -> CriticEvaluation:
    """
    Evaluates whether the gathered evidence answers the research question adequately.
    If not, it suggests new queries.
    """
    evidence_text = ""
    for i, item in enumerate(claims_and_evidence):
        evidence_text += f"Claim {i+1}: {item['claim']} (Confidence: {item['confidence']})\n"
        
    prompt = f"""
    You are an expert Research Critic.
    Evaluate the following evidence gathered for this research question: "{question}"
    
    Research Dimensions: {json.dumps(plan.get('research_dimensions', []))}
    
    Evidence Claims:
    {evidence_text}
    
    Determine if the evidence is sufficient to write a comprehensive report. 
    Identify any major contradictions or missing information.
    If insufficient, provide 2-3 additional search queries to run.
    
    Return strictly JSON matching this structure:
    {{
      "is_sufficient": true,
      "missing_information": "string",
      "contradictions": ["string"],
      "additional_queries": ["string"]
    }}
    """
    
    messages = [
        {"role": "system", "content": "You are a critical research evaluator designed to output strictly JSON."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        data = generate_structured_completion(messages=messages)
        return CriticEvaluation(**data)
    except Exception as e:
        print(f"Error in critic: {e}")
        # Default to sufficient to avoid infinite loops on error
        return CriticEvaluation(is_sufficient=True, missing_information="", contradictions=[], additional_queries=[])
