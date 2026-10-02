import json
from pydantic import BaseModel, Field
from typing import List
from app.services.llm_service import generate_structured_completion

class ResearchPlan(BaseModel):
    main_question: str = Field(description="The original user question or a refined version of it")
    sub_questions: List[str] = Field(description="List of smaller questions to research")
    research_dimensions: List[str] = Field(description="Key dimensions or aspects to cover (e.g. 'market size', 'technology')")

async def create_research_plan(user_question: str) -> ResearchPlan:
    """
    Calls Groq to break down the user's question into sub-questions and dimensions.
    """
    prompt = f"""
    You are an expert AI Research Planner.
    The user wants to research the following topic: "{user_question}"
    
    Your task is to break this complex question into a structured research plan.
    Identify the main question, 3-5 sub-questions that need to be answered, 
    and 3-5 key research dimensions (e.g., market size, technical challenges, competitors).
    
    Return the output strictly in JSON format matching this structure:
    {{
      "main_question": "string",
      "sub_questions": ["string"],
      "research_dimensions": ["string"]
    }}
    """
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant designed to output strictly JSON."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        plan_dict = generate_structured_completion(messages=messages)
        return ResearchPlan(**plan_dict)
    except Exception as e:
        print(f"Error parsing planner output: {e}")
        # fallback plan
        return ResearchPlan(
            main_question=user_question,
            sub_questions=[user_question],
            research_dimensions=["General Analysis"]
        )
