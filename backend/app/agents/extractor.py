import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from google.genai import types
from .planner import get_gemini_client

async def fetch_page_content(url: str) -> str:
    """
    Fetches the HTML of a webpage and extracts clean text using BeautifulSoup.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return ""
                html = await response.text()
                
                soup = BeautifulSoup(html, "html.parser")
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "header", "footer"]):
                    script.extract()
                    
                text = soup.get_text(separator=" ", strip=True)
                return text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Splits text into chunks with overlap.
    """
    if not text:
        return []
    
    # Very basic chunking
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Gets text embeddings using Gemini.
    """
    if not texts:
        return []
        
    client = get_gemini_client()
    try:
        # Gemini text-embedding-004
        result = client.models.embed_content(
            model='text-embedding-004',
            contents=texts,
        )
        # Result contains a list of embeddings
        return [e.values for e in result.embeddings]
    except Exception as e:
        print(f"Error getting embeddings: {e}")
        # Return empty list or fallback to zero vectors for error handling
        return []
