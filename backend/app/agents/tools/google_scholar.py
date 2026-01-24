"""
Google Scholar API Tool via SerpAPI

Search and retrieve academic papers from Google Scholar using SerpAPI.
"""

import httpx
from typing import List, Optional
from app.config import get_settings

settings = get_settings()

SERPAPI_BASE_URL = "https://serpapi.com/search"


async def search_google_scholar(
    query: str,
    limit: int = 20,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> List[dict]:
    """
    Search for papers on Google Scholar via SerpAPI.
    
    Args:
        query: Search query string
        limit: Maximum number of results (SerpAPI returns up to 20 per page)
        year_from: Only include papers from this year onwards
        year_to: Only include papers up to this year
        
    Returns:
        List of paper dictionaries with metadata
    """
    if not settings.serpapi_key:
        print("Warning: SERPAPI_KEY not set, Google Scholar search unavailable")
        return []
    
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": settings.serpapi_key,
        "num": min(limit, 20),  # SerpAPI max per page
    }
    
    # Add year filter if specified
    if year_from and year_to:
        params["as_ylo"] = year_from
        params["as_yhi"] = year_to
    elif year_from:
        params["as_ylo"] = year_from
    elif year_to:
        params["as_yhi"] = year_to
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(SERPAPI_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for result in data.get("organic_results", []):
                # Extract year from publication info if available
                year = None
                pub_info = result.get("publication_info", {})
                summary = pub_info.get("summary", "")
                # Try to extract year (usually appears as ", YYYY -" or "YYYY")
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', summary)
                if year_match:
                    year = int(year_match.group())
                
                papers.append({
                    "id": result.get("result_id", result.get("position", "")),
                    "title": result.get("title", ""),
                    "abstract": result.get("snippet", ""),
                    "year": year,
                    "authors": pub_info.get("authors", [{}])[0].get("name", "") if pub_info.get("authors") else "",
                    "venue": pub_info.get("summary", "").split(" - ")[0] if " - " in pub_info.get("summary", "") else None,
                    "citation_count": result.get("inline_links", {}).get("cited_by", {}).get("total"),
                    "url": result.get("link", ""),
                    "pdf_url": result.get("resources", [{}])[0].get("link") if result.get("resources") else None,
                    "provider": "google_scholar",
                })
            
            return papers
            
        except httpx.HTTPError as e:
            print(f"Google Scholar (SerpAPI) error: {e}")
            return []


async def get_paper_citations(
    citation_id: str,
    limit: int = 20,
) -> List[dict]:
    """
    Get papers that cite a specific paper.
    
    Args:
        citation_id: The cites parameter from a previous search result
        limit: Maximum number of results
        
    Returns:
        List of citing paper dictionaries
    """
    if not settings.serpapi_key:
        return []
    
    params = {
        "engine": "google_scholar",
        "cites": citation_id,
        "api_key": settings.serpapi_key,
        "num": min(limit, 20),
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(SERPAPI_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            for result in data.get("organic_results", []):
                papers.append({
                    "id": result.get("result_id", ""),
                    "title": result.get("title", ""),
                    "abstract": result.get("snippet", ""),
                    "url": result.get("link", ""),
                    "provider": "google_scholar",
                })
            
            return papers
            
        except httpx.HTTPError as e:
            print(f"Google Scholar citations error: {e}")
            return []


async def get_author_profile(author_id: str) -> Optional[dict]:
    """
    Get author profile from Google Scholar.
    
    Args:
        author_id: Google Scholar author ID
        
    Returns:
        Author profile dictionary or None
    """
    if not settings.serpapi_key:
        return None
    
    params = {
        "engine": "google_scholar_author",
        "author_id": author_id,
        "api_key": settings.serpapi_key,
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(SERPAPI_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            author = data.get("author", {})
            return {
                "id": author_id,
                "name": author.get("name", ""),
                "affiliations": author.get("affiliations", ""),
                "email": author.get("email", ""),
                "interests": [i.get("title", "") for i in data.get("interests", [])],
                "citation_count": data.get("cited_by", {}).get("table", [{}])[0].get("citations", {}).get("all"),
                "h_index": data.get("cited_by", {}).get("table", [{}])[1].get("h_index", {}).get("all") if len(data.get("cited_by", {}).get("table", [])) > 1 else None,
            }
            
        except httpx.HTTPError as e:
            print(f"Google Scholar author error: {e}")
            return None
