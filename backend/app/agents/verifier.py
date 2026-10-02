import json
import re
from typing import List, Dict, Any
from app.services.llm_service import generate_completion

async def verify_citations(report_markdown: str, claims_and_evidence: List[Dict[str, Any]]) -> str:
    """
    Verifies that all claims in the report are backed by the provided evidence.
    Flags any unsupported claims.
    """
    evidence_text = ""
    for i, item in enumerate(claims_and_evidence):
        evidence_text += f"Claim {i+1}: {item['claim']} (Source: {item['source_url']})\n"
        
    prompt = f"""
    You are an expert Citation Verifier.
    Review the following research report and ensure that all major factual claims are supported by the provided evidence.
    
    If a claim in the report is NOT supported by the evidence, append a warning like: 
    "**[UNVERIFIED CLAIM]**" next to it in the report text.
    
    Do not change the structure or flow of the report, just add the warning tags where necessary.
    Return the fully updated markdown report.
    
    Report:
    {report_markdown}
    
    Valid Evidence:
    {evidence_text}
    """
    
    messages = [
        {"role": "system", "content": "You are a precise citation verifier."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        verified_report = generate_completion(messages=messages)
        return verified_report
    except Exception as e:
        print(f"Error in citation verifier: {e}")
        return report_markdown
