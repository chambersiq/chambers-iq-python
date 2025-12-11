from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from app.services.external.indian_kanoon import IndianKanoonClient
from app.core.config import settings

# Initialize client
client = IndianKanoonClient(api_token=settings.INDIAN_KANOON_API_TOKEN)

@tool
async def search_indian_kanoon(query: str, max_results: int = 5):
    """
    Search for legal documents, case laws, or acts using Indian Kanoon API.
    Useful for finding precedents or statute sections.
    """
    results = await client.search(query=query, maxpages=1)
    # Simple formatting of results for the agent
    return results.get("docs", [])[:max_results]

@tool
async def get_document_text(doc_id: int):
    """
    Retrieve the full text or summary of a specific legal document by its ID.
    Use this after finding a relevant document via search.
    """
    # Fetch with citations to get a complete picture
    doc = await client.get_document(doc_id, maxcites=5, maxcitedby=5)
    return doc

citation_tools = [search_indian_kanoon, get_document_text]
