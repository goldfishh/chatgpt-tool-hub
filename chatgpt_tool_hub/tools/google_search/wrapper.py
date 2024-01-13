"""Util that calls Google Search."""
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Extra, root_validator

from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from ..web_requests import filter_text

class OutputType(str, Enum):
    Text = "text"
    JSON = "json"

class GoogleSearchAPIWrapper(BaseModel):
    """Wrapper for Google Search API."""

    search_engine: Any
    google_api_key: Optional[str] = None
    google_cse_id: Optional[str] = None

    google_top_k_results: int = 2
    google_simple: bool = True
    google_output_type: OutputType = OutputType.Text

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

        values["google_top_k_results"] = get_from_dict_or_env(
            values, 'google_top_k_results', "GOOGLE_TOP_K_RESULTS", 2
        )

        values["google_simple"] = get_from_dict_or_env(
            values, 'google_simple', "GOOGLE_SIMPLE", True
        )

        values["google_output_type"] = get_from_dict_or_env(
            values, 'google_output_type', "google_output_type", OutputType.Text
        )

        return values

    def run(self, query: str) -> str:
        """(for normal result): Run query through GoogleSearch and parse result."""
        if self.google_output_type == OutputType.JSON:
            return self.to_json(query)
        results = self._google_search_results(query, num=self.google_top_k_results)
        if len(results) == 0:
            return "No good Google Search Result was found"
        LOG.debug(f"[google_search] output: {str(results)}")

        _contents = []
        for idx, result in enumerate(results):
            _header = f"{idx+1}. 《{filter_text(result.get('title', ''))}》" if not self.google_simple else f"《{filter_text(result.get('title', ''))}》"
            _body = f"{filter_text(result.get('snippet', ''))}"
            _link = f"{result.get('link', '')}"
            _contents.append(f"{_header}\n{_body}\n[{_link}]\n\n---\n")
        return "\n".join(_contents)

    def to_json(self, query: str) -> List[Dict]:
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
        results = self._google_search_results(query, num=self.google_top_k_results)
        if len(results) == 0:
            return [{"Result": "No good Google Search Result was found"}]
        LOG.debug(f"[google_search] output: {str(results)}")

        for result in results:
            metadata_result = {
                "title": filter_text(result["title"]),
                "link": result["link"],
            }
            if "snippet" in result:
                metadata_result["snippet"] = filter_text(result["snippet"])
            metadata_results.append(metadata_result)
        return metadata_results
