"""Util that calls Bing Search."""
import json
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, model_validator

from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from ..web_requests import filter_text
from ..web_requests.wrapper import RequestsWrapper

class OutputType(str, Enum):
    Text = "text"
    JSON = "json"

class BingSearchAPIWrapper(BaseModel):
    """Wrapper for Bing Search API."""

    bing_subscription_key: Optional[str]
    bing_search_url: Optional[str]
    
    bing_search_top_k_results: Optional[int]
    bing_search_simple: Optional[bool]
    bing_search_output_type: Optional[OutputType]

    class Config:
        """Configuration for this pydantic object."""

        extra = 'ignore'

    def _bing_search_results(self, search_term: str, count: int) -> List[dict]:
        headers = {"Ocp-Apim-Subscription-Key": self.bing_subscription_key}
        params = {
            "q": search_term,
            "count": count,
            "textDecorations": True,
            "textFormat": "HTML",
        }
        response = RequestsWrapper(headers=headers).get(self.bing_search_url, params=params, raise_for_status=True)

        search_results = json.loads(response)
        try:
            result = search_results["webPages"]["value"]
            LOG.debug(f"[bing_search] output: {str(result)}")
        except Exception as e:
            result = []
            LOG.error(f"[bing_search] {repr(e)}")
        return result

    @model_validator(mode='before')
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and endpoint exists in environment."""

        values["bing_subscription_key"] = get_from_dict_or_env(
            values, "bing_subscription_key", "BING_SUBSCRIPTION_KEY"
        )

        values["bing_search_url"] = get_from_dict_or_env(
            values, "bing_search_url", "BING_SEARCH_URL",
            default="https://api.bing.microsoft.com/v7.0/search",
        )

        values["bing_search_top_k_results"] = get_from_dict_or_env(
            values, 'bing_search_top_k_results', "BING_SEARCH_TOP_K_RESULTS", 2)

        values["bing_search_simple"] = get_from_dict_or_env(
            values, 'bing_search_simple', "BING_SEARCH_SIMPLE", True)

        values["bing_search_output_type"] = get_from_dict_or_env(
            values, 'bing_search_output_type', "BING_SEARCH_OUTPUT_TYPE", 
            OutputType.Text)

        return values

    def run(self, query: str) -> str:
        """Run query through BingSearchTool and parse result."""
        if self.bing_search_output_type == OutputType.JSON:
            return self.to_json(query)
        results = self._bing_search_results(query, count=self.bing_search_top_k_results)
        if len(results) == 0:
            return "No good Bing Search Result was found"
        
        _contents = []
        for idx, result in enumerate(results):
            _header = f"{idx+1}. 《{filter_text(result.get('name', ''))}》" if not self.bing_search_simple else f"《{filter_text(result.get('name', ''))}》"
            _body = f"{filter_text(result.get('snippet', ''))}"
            _link = f"{result.get('url', '')}"
            _contents.append(f"{_header}\n{_body}\n[{_link}]\n\n---\n")
        return "\n".join(_contents)

    def to_json(self, query: str) -> List[Dict]:
        """(for json result): Run query through BingSearchTool and return metadata.

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
        results = self._bing_search_results(query, count=self.bing_search_top_k_results)
        if len(results) == 0:
            return [{"Result": "No good Bing Search Result was found"}]
        for result in results:
            metadata_result = {
                "snippet": filter_text(result["snippet"]),
                "title": filter_text(result["name"]),
                "link": result["url"],
                "cache": result["cachedPageUrl"],
            }
            metadata_results.append(metadata_result)

        return metadata_results


if __name__ == "__main__":
    pass
