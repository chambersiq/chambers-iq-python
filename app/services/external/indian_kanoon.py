from typing import Dict, Any, Optional
import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class IndianKanoonClient:
    """
    Client for interacting with the Indian Kanoon API.
    Documentation: https://api.indiankanoon.org/
    """
    BASE_URL = "https://api.indiankanoon.org"

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or settings.INDIAN_KANOON_API_TOKEN
        if not self.api_token:
            logger.warning("INDIAN_KANOON_API_TOKEN is not set. API calls will fail.")

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_token:
            raise ValueError("API Token is required for Indian Kanoon API")
        return {
            "Authorization": f"Token {self.api_token}",
            "Accept": "application/json"
        }

    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Helper method to make authenticated requests to the API.
        """
        url = f"{self.BASE_URL}/{endpoint}"
        headers = self._get_headers()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 403:
                     raise ValueError("Invalid API Token or Unauthorized access")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error occurred: {str(e)}")
                raise

    async def search(self, query: str, pagenum: int = 0, maxpages: int = 1) -> Dict[str, Any]:
        """
        Search for documents using a query string.
        
        Args:
            query (str): The search query (e.g., "freedom of speech").
            pagenum (int): Page number, starting from 0.
            maxpages (int): Max search result pages to retrieve (default 1).
            
        Returns:
            Dict[str, Any]: Search results including docs list and categories.
        """
        endpoint = "search/"
        params = {
            "formInput": query,
            "pagenum": pagenum,
            "maxpages": maxpages
        }
        return await self._make_request(endpoint, params)

    async def get_document(self, doc_id: int, maxcites: int = 10, maxcitedby: int = 10) -> Dict[str, Any]:
        """
        Retrieve the full text of a document by its ID, with optional citation limits.
        
        Args:
            doc_id (int): The unique ID of the document.
            maxcites (int): Max number of cited documents to retrieve (default 10, max 50).
            maxcitedby (int): Max number of documents citing this one to retrieve (default 10, max 50).
            
        Returns:
            Dict[str, Any]: Document details including title, doc, citeList, citedbyList.
        """
        endpoint = f"doc/{doc_id}/"
        params = {
            "maxcites": maxcites,
            "maxcitedby": maxcitedby
        }
        return await self._make_request(endpoint, params)

    async def get_court_copy(self, doc_id: int) -> Dict[str, Any]:
        """
        Retrieve the original court copy of a document.
        
        Args:
            doc_id (int): The unique ID of the document.
            
        Returns:
             Dict[str, Any]: Response containing link or data for the original copy.
        """
        endpoint = f"origdoc/{doc_id}/"
        return await self._make_request(endpoint)

    async def get_document_fragments(self, doc_id: int, query: str) -> Dict[str, Any]:
        """
        Retrieve fragments of a document that match a specific query.
        Useful for highlighting search terms within a document.
        
        Args:
            doc_id (int): The unique ID of the document.
            query (str): The query string to highlight/find fragments for.
            
        Returns:
            Dict[str, Any]: Document fragments.
        """
        endpoint = f"docfragment/{doc_id}/"
        params = {
            "formInput": query
        }
        return await self._make_request(endpoint, params)

    async def get_document_meta(self, doc_id: int, maxcites: int = 10, maxcitedby: int = 10) -> Dict[str, Any]:
        """
        Retrieve metadata for a document without the full content.
        
        Args:
            doc_id (int): The unique ID of the document.
            maxcites (int): Max number of cited documents (default 10).
            maxcitedby (int): Max number of citing documents (default 10).
            
        Returns:
            Dict[str, Any]: Document metadata.
        """
        endpoint = f"docmeta/{doc_id}/"
        params = {
            "maxcites": maxcites,
            "maxcitedby": maxcitedby
        }
        return await self._make_request(endpoint, params)
