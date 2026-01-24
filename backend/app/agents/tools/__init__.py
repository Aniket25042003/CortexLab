"""Agent Tools Package"""

from app.agents.tools.google_scholar import (
    search_google_scholar,
    get_paper_citations,
    get_author_profile,
)
from app.agents.tools.web_search import web_search

__all__ = [
    # Google Scholar (SerpAPI)
    "search_google_scholar",
    "get_paper_citations",
    "get_author_profile",
    # Web Search
    "web_search",
]
