import json
import asyncio
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services.llm_service import generate_structured_completion
from app.services.search_service import execute_search

class SearchQueries(BaseModel):
    queries: List[str] = Field(description="List of exact search engine queries to execute")

async def generate_search_queries(sub_questions: List[str], dimensions: List[str]) -> List[str]:
    """
    Uses Groq to generate optimized search engine queries based on the research plan.
    """
    prompt = f"""
    You are an expert search engine operator.
    Given these sub-questions: {json.dumps(sub_questions)}
    And these dimensions: {json.dumps(dimensions)}
    
    Generate 4-6 highly effective search queries to find the most relevant and authoritative information.
    Keep them concise and keyword-focused.
    
    Return strictly JSON in this format:
    {{
      "queries": ["query1", "query2"]
    }}
    """
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant designed to output strictly JSON."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        data = generate_structured_completion(messages=messages)
        return data.get("queries", [])
    except:
        return sub_questions

async def search_and_deduplicate(queries: List[str], max_results_per_query: int = 3) -> List[Dict[str, Any]]:
    """
    Runs searches in parallel using Tavily and deduplicates URLs.
    """
    loop = asyncio.get_running_loop()
    
    # Run synchronous Tavily search in thread pool
    tasks = [
        loop.run_in_executor(None, execute_search, query, max_results_per_query)
        for query in queries
    ]
    
    results = await asyncio.gather(*tasks)
    
    seen_urls = set()
    unique_sources = []
    
    for query_result in results:
        if not isinstance(query_result, list):
            continue
            
        for item in query_result:
            url = item.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "publisher": item.get("publisher", ""),
                    "published_at": item.get("published_at", "")
                })
                
    return unique_sources

