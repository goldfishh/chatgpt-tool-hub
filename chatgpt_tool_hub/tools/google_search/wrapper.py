"""Util that calls Google Search."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Extra, root_validator

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.tools.web_requests import filter_text


class GoogleSearchAPIWrapper(BaseModel):
    """Wrapper for Google Search API."""

    search_engine: Any
    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None
    top_k_results: int = 2

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.ignore

    def _google_search_results(self, search_term: str, **kwargs: Any) -> List[dict]:
        res = (
            self.search_engine.cse()
            .list(q=search_term, cx=self.google_cse_id, **kwargs)
            .execute()
        )
        return res.get("items", [])

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        google_api_key = get_from_dict_or_env(
            values, "google_api_key", "GOOGLE_API_KEY"
        )
        values["google_api_key"] = google_api_key

        google_cse_id = get_from_dict_or_env(values, "google_cse_id", "GOOGLE_CSE_ID")
        values["google_cse_id"] = google_cse_id

        try:
            from googleapiclient.discovery import build

        except ImportError:
            raise ImportError(
                "google-api-python-client is not installed. "
                "Please install it with `pip install google-api-python-client`"
            )

        service = build("customsearch", "v1", developerKey=google_api_key)
        values["search_engine"] = service

        values["top_k_results"] = get_from_dict_or_env(
            values, 'top_k_results', "TOP_K_RESULTS", 2
        )

        return values

    def run(self, query: str) -> str:
        """(for normal result): Run query through GoogleSearch and parse result."""
        results = self._google_search_results(query, num=self.top_k_results)
        if len(results) == 0:
            return "No good Google Search Result was found"

        snippets = [
            filter_text(result["snippet"])
            for result in results
            if "snippet" in result
        ]
        LOG.debug(f"[GoogleSearch] output: {snippets}")
        return " ".join(snippets)

    def results(self, query: str) -> List[Dict]:
        """(for json result): Run query through GoogleSearch and return metadata.

        Args:
            query: The query to search for.
            num_results: The number of results to return.

        Returns:
            A list of dictionaries with the following keys:
                snippet - The description of the result.
                title - The title of the result.
                link - The link to the result.
        """
        metadata_results = []
        results = self._google_search_results(query, num=self.top_k_results)
        if len(results) == 0:
            return [{"Result": "No good Google Search Result was found"}]

        for result in results:
            metadata_result = {
                "title": result["title"],
                "link": result["link"],
            }
            if "snippet" in result:
                metadata_result["snippet"] = filter_text(result["snippet"])
            metadata_results.append(metadata_result)
        LOG.debug(f"[GoogleSearch] output: {metadata_results}")
        return metadata_results
