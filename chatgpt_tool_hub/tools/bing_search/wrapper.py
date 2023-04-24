"""Util that calls Bing Search."""
import json
from typing import Dict, List

from pydantic import BaseModel, Extra, validator, root_validator

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.tools.web_requests import filter_text
from chatgpt_tool_hub.tools.web_requests.wrapper import RequestsWrapper


class BingSearchAPIWrapper(BaseModel):
    """Wrapper for Bing Search API."""

    bing_subscription_key: str
    bing_search_url: str
    top_k_results: int = 2

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.ignore

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

    @root_validator(pre=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and endpoint exists in environment."""

        values["bing_subscription_key"] = get_from_dict_or_env(
            values, "bing_subscription_key", "BING_SUBSCRIPTION_KEY"
        )

        values["bing_search_url"] = get_from_dict_or_env(
            values,
            "bing_search_url",
            "BING_SEARCH_URL",
            default="https://api.bing.microsoft.com/v7.0/search",
        )

        values["top_k_results"] = get_from_dict_or_env(
            values, 'top_k_results', "TOP_K_RESULTS", 2
        )

        return values

    def run(self, query: str) -> str:
        """Run query through BingSearch and parse result."""
        results = self._bing_search_results(query, count=self.top_k_results)
        if len(results) == 0:
            return "No good Bing Search Result was found"

        snippets = [filter_text(result["snippet"]) for result in results]
        return " ".join(snippets)

    def results(self, query: str, num_results: int) -> List[Dict]:
        """(for json result): Run query through BingSearch and return metadata.

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
        results = self._bing_search_results(query, count=num_results)
        if len(results) == 0:
            return [{"Result": "No good Bing Search Result was found"}]
        for result in results:
            metadata_result = {
                "snippet": result["snippet"],
                "title": result["name"],
                "link": result["url"],
            }
            metadata_results.append(metadata_result)

        return metadata_results
