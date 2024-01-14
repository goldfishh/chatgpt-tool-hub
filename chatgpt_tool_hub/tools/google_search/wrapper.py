"""Util that calls Google Search."""
import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, model_validator

from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from ..web_requests import filter_text

class OutputType(str, Enum):
    Text = "text"
    JSON = "json"

class GoogleSearchAPIWrapper(BaseModel):
    """Wrapper for Google Search API."""

    search_engine: Any
    google_api_key: Optional[str]
    google_cse_id: Optional[str]

    google_top_k_results: Optional[int]
    google_simple: Optional[bool]
    google_output_type: Optional[OutputType]

    class Config:
        """Configuration for this pydantic object."""

        extra = 'ignore'

    def _google_search_results(self, search_term: str, **kwargs: Any) -> List[dict]:
        res = (
            self.search_engine.cse()
            .list(q=search_term, cx=self.google_cse_id, **kwargs)
            .execute()
        )
        return res.get("items", [])

    @model_validator(mode='before')
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        google_api_key = get_from_dict_or_env(
            values, "google_api_key", "GOOGLE_API_KEY"
        )
        values["google_api_key"] = google_api_key

        values["google_cse_id"] = get_from_dict_or_env(values, "google_cse_id", "GOOGLE_CSE_ID")

        proxy = get_from_dict_or_env(values, "proxy", "PROXY", "")

        try:
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "google-api-python-client is not installed. "
                "Please install it with `pip install google-api-python-client`"
            )
        
        def _parse_proxy_url(proxy_url):
            # 定义正则表达式，匹配代理地址和端口号
            pattern = re.compile(r'(?:(?P<protocol>https?://)?(?P<host>[^:/]+)(?::(?P<port>\d+))?|(?P<host_only>[^:/]+))')
            match = pattern.match(proxy_url)

            if match:
                groups = match.groupdict()
                host = groups.get('host') or groups.get('host_only', '')
                port = groups.get('port', '80')  # 默认端口为 80

                return host, int(port)
            else:
                return None

        if proxy and _parse_proxy_url(proxy):
            import httplib2
            import google_auth_httplib2
            from google.auth.credentials import AnonymousCredentials

            PROXY_IP, PROXY_PORT = _parse_proxy_url(proxy)
            http = httplib2.Http(proxy_info=httplib2.ProxyInfo(
                        httplib2.socks.PROXY_TYPE_HTTP, PROXY_IP, PROXY_PORT
            ))

            authorized_http = google_auth_httplib2.AuthorizedHttp(AnonymousCredentials(), http=http)

            service = build("customsearch", "v1", developerKey=google_api_key, http=authorized_http)
        else:
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
