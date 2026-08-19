import json
from typing import List, Dict, Any
from google.genai import types
from .planner import get_gemini_client

async def generate_research_report(question: str, plan: Dict[str, Any], claims_and_evidence: List[Dict[str, Any]]) -> str:
    """
    Synthesizes the gathered evidence into a structured markdown report.
    """
    client = get_gemini_client()
    
    # Format evidence for the prompt
    evidence_text = ""
    for i, item in enumerate(claims_and_evidence):
        evidence_text += f"Claim {i+1}: {item['claim']} (Confidence: {item['confidence']})\n"
        evidence_text += f"Source URL: {item['source_url']}\n"
        evidence_text += f"Supporting text: {item['evidence_text']}\n\n"
        
    prompt = f"""
    You are an expert AI Research Analyst.
    Write a comprehensive, professional research report for the following question:
    "{question}"
    
    Research Dimensions: {json.dumps(plan.get('research_dimensions', []))}
    
    You must use the following extracted evidence to write the report. 
    Every major claim in the report MUST include an inline citation to the Source URL.
    Format your response in Markdown.
    
    Structure the report as follows:
    - # Executive Summary
    - # Key Findings
    - # Detailed Analysis (organized by dimensions)
    - # Contradictions / Uncertainty (if any conflicting evidence exists)
    - # Conclusion
    - # Sources (A list of references with URLs)
    
    Evidence:
    {evidence_text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"Error generating report: {e}")
        return "# Error\nFailed to generate report."
