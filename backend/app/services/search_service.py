import os
import logging
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
from tavily import TavilyClient
from app.core.config import settings

logger = logging.getLogger(__name__)

_tavily_client: Optional[TavilyClient] = None

def get_tavily_client() -> Optional[TavilyClient]:
    global _tavily_client
    api_key = settings.TAVILY_API_KEY or os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        logger.warning("TAVILY_API_KEY is not configured. Web search will return no results.")
        return None
    if _tavily_client is None:
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client

def execute_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the web using Tavily API.
    Returns normalized results.
    """
    client = get_tavily_client()
    if not client:
        return []

    try:
        response = client.search(query=query, search_depth="basic", max_results=max_results)
        results = response.get("results", [])
        
        normalized_results = []
        for res in results:
            url = res.get("url", "")
            publisher = ""
            if url:
                try:
                    publisher = urlparse(url).netloc.replace("www.", "")
                except Exception:
                    publisher = ""

            normalized_results.append({
                "title": res.get("title", ""),
                "url": url,
                "content": res.get("content", ""),
                "publisher": publisher,
                "published_at": res.get("published_date", "")
            })
            
        return normalized_results
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            logger.error("Tavily API returned 401 Unauthorized. Please verify your TAVILY_API_KEY.")
        else:
            logger.error(f"Error during Tavily search for query '{query}': {error_msg}")
        return []

