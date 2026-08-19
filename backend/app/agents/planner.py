import os
import json
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from app.core.config import settings
from typing import List

class ResearchPlan(BaseModel):
    main_question: str = Field(description="The original user question or a refined version of it")
    sub_questions: List[str] = Field(description="List of smaller questions to research")
    research_dimensions: List[str] = Field(description="Key dimensions or aspects to cover (e.g. 'market size', 'technology')")

def get_gemini_client():
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=api_key)

async def create_research_plan(user_question: str) -> ResearchPlan:
    """
    Calls Gemini to break down the user's question into sub-questions and dimensions.
    """
    client = get_gemini_client()
    
    prompt = f"""
    You are an expert AI Research Planner.
    The user wants to research the following topic: "{user_question}"
    
    Your task is to break this complex question into a structured research plan.
    Identify the main question, 3-5 sub-questions that need to be answered, 
    and 3-5 key research dimensions (e.g., market size, technical challenges, competitors).
    """
    
    # We use Structured Outputs if available, otherwise just JSON
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResearchPlan,
        ),
    )
    
    try:
        plan_dict = json.loads(response.text)
        return ResearchPlan(**plan_dict)
    except Exception as e:
        print(f"Error parsing planner output: {e}")
        # fallback plan
        return ResearchPlan(
            main_question=user_question,
            sub_questions=[user_question],
            research_dimensions=["General Analysis"]
        )
