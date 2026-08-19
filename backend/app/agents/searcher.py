import os
import json
import asyncio
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from google.genai import types
from duckduckgo_search import DDGS
from .planner import get_gemini_client

class SearchQueries(BaseModel):
    queries: List[str] = Field(description="List of exact search engine queries to execute")

async def generate_search_queries(sub_questions: List[str], dimensions: List[str]) -> List[str]:
    """
    Uses Gemini to generate optimized search engine queries based on the research plan.
    """
    client = get_gemini_client()
    
    prompt = f"""
    You are an expert search engine operator.
    Given these sub-questions: {json.dumps(sub_questions)}
    And these dimensions: {json.dumps(dimensions)}
    
    Generate 4-6 highly effective Google/DuckDuckGo search queries to find the most relevant and authoritative information.
    Keep them concise and keyword-focused.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SearchQueries,
        ),
    )
    
    try:
        data = json.loads(response.text)
        return data.get("queries", [])
    except:
        return sub_questions

def execute_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Executes a web search using DuckDuckGo.
    """
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title"),
                    "url": r.get("href"),
                    "snippet": r.get("body")
                })
    except Exception as e:
        print(f"Search failed for query '{query}': {e}")
    return results

async def search_and_deduplicate(queries: List[str], max_results_per_query: int = 3) -> List[Dict[str, Any]]:
    """
    Runs searches in parallel and deduplicates URLs.
    """
    loop = asyncio.get_event_loop()
    
    # Run synchronous DDGS in thread pool
    tasks = [
        loop.run_in_executor(None, execute_search, query, max_results_per_query)
        for query in queries
    ]
    
    results = await asyncio.gather(*tasks)
    
    seen_urls = set()
    unique_sources = []
    
    for query_result in results:
        for item in query_result:
            url = item.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(item)
                
    return unique_sources
