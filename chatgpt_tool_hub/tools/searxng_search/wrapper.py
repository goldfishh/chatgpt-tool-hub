"""Utility for using SearxNG meta search API.

the search API refer to https://docs.searxng.org/dev/search_api.html

Quick Start
-----------

In order to use this utility you need to provide the searx host. This can be done
by passing the named parameter :attr:`searxng_search_host <SearxSearchWrapper.searxng_search_host>`
or exporting the environment variable SEARX_SEARCH_HOST.

1. https://docs.searxng.org/admin/installation-searxng.html#installation-basic

2. change `/etc/searxng/settings.yml`
search.formats: ["html", "json"]
server.bind_address: "0.0.0.0"
server.limiter: false

You can now use the ``search`` instance to query the searx API.

See `SearxNG Configured Engines
<https://docs.searxng.org/admin/engines/configured_engines.html>`_ and
`SearxNG Search Syntax <https://docs.searxng.org/user/index.html#id1>`_
for more details.

Notes
-----
This wrapper is based on the SearxNG fork https://github.com/searxng/searxng which is
better maintained than the original Searx project and offers more features.
"""

import json
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field, PrivateAttr, model_validator, field_validator
from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from ..web_requests import RequestsWrapper, filter_text


def _get_default_params() -> dict:
    return {"language": "zh", "format": "json"}


class SearxResults(dict):
    """Dict like wrapper around search api results."""

    _data = ""

    def __init__(self, data: str):
        """Take a raw result from Searx and make it into a dict like object."""
        json_data = json.loads(data)
        super().__init__(json_data)
        self.__dict__ = self

    def __str__(self) -> str:
        """Text representation of searx result."""
        return self._data

    @property
    def results(self) -> Any:
        """Silence mypy for accessing this field.

        :meta private:
        """
        return self.get("results")

    @property
    def answers(self) -> Any:
        """Helper accessor on the json result."""
        return self.get("answers")


class OutputType(str, Enum):
    Text = "text"
    JSON = "json"

class SearxSearchWrapper(BaseModel):
    """Wrapper for Searx API.

    To use you need to provide the searx host by passing the named parameter
    ``searxng_search_host`` or exporting the environment variable ``SEARX_SEARCH_HOST``.

    In some situations you might want to disable SSL verification, for example
    if you are running searx locally. You can do this by passing the named parameter
    ``unsecure``. You can also pass the host url scheme as ``http`` to disable SSL.

    Example:
        .. code-block:: python

            from chatgpt-tool-hub.tools.searxng_search.wrapper import SearxSearchWrapper
            searx = SearxSearchWrapper(searxng_search_host="http://localhost:8888")

    Example with SSL disabled:
        .. code-block:: python

            from chatgpt-tool-hub.tools.searxng_search.wrapper import SearxSearchWrapper
            # note the unsecure parameter is not needed if you pass the url scheme as
            # http
            searx = SearxSearchWrapper(searxng_search_host="http://localhost:8888",
                                                    unsecure=True)


    """

    _result: SearxResults = PrivateAttr()
    searxng_search_host: Optional[str] = None
    searxng_search_output_type: OutputType = OutputType.Text
    unsecure: bool = False
    params: dict = Field(default_factory=_get_default_params)
    headers: Optional[dict] = dict()
    engines: Optional[List[str]] = []
    categories: Optional[List[str]] = []
    query_suffix: Optional[str] = ""
    searxng_search_top_k_results: int = 2
    aiosession: Optional[Any] = None

    @field_validator("unsecure")
    def disable_ssl_warnings(cls, v: bool) -> bool:
        """Disable SSL warnings."""
        if v:
            try:
                import urllib3

                urllib3.disable_warnings()
            except ImportError as e:
                print(e)
        return v

    @model_validator(mode='before')
    def validate_params(cls, values: Dict) -> Dict:
        """Validate that custom searx params are merged with default ones."""
        values["params"] = {**_get_default_params(), **values["params"]} if values.get("params") else {**_get_default_params()}

        if engines := values.get("engines"):
            values["params"]["engines"] = ",".join(engines)

        if categories := values.get("categories"):
            values["params"]["categories"] = ",".join(categories)

        searxng_search_host = get_from_dict_or_env(values, "searxng_search_host", "SEARXNG_SEARCH_HOST")
        if not searxng_search_host.startswith("http"):
            print(
                f"Warning: missing the url scheme on host \
                ! assuming secure https://{searxng_search_host} "
            )
            searxng_search_host = f"https://{searxng_search_host}"
        elif searxng_search_host.startswith("http://"):
            values["unsecure"] = True
            cls.disable_ssl_warnings(True)
        values["searxng_search_host"] = searxng_search_host

        values["searxng_search_top_k_results"] = get_from_dict_or_env(
            values, 'searxng_search_top_k_results', "SEARXNG_SEARCH_TOP_K_RESULTS", 2
        )

        values["searxng_search_output_type"] = get_from_dict_or_env(
            values, 'searxng_search_output_type', "SEARXNG_SEARCH_OUTPUT_TYPE", OutputType.Text
        )

        return values

    class Config:
        """Configuration for this pydantic object."""

        extra = 'ignore'

    def _searx_api_query(self, params: dict) -> SearxResults:
        """Actual request to searx API."""
        requests_wrapper = RequestsWrapper(headers=self.headers, proxy="")
        raw_result = requests_wrapper.get(self.searxng_search_host, params=params,
                                          raise_for_status=True, verify=not self.unsecure)
        # test if http result is ok
        res = SearxResults(raw_result)
        self._result = res
        return res

    async def _asearx_api_query(self, params: dict) -> SearxResults:
        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.searxng_search_host,
                    headers=self.headers,
                    params=params,
                    ssl=(lambda: False if self.unsecure else None)(),
                ) as response:
                    if not response.ok:
                        raise ValueError("Searx API returned an error: ", response.text)
                    result = SearxResults(await response.text())
                    self._result = result
        else:
            async with self.aiosession.get(
                self.searxng_search_host,
                headers=self.headers,
                params=params,
                verify=not self.unsecure,
            ) as response:
                if not response.ok:
                    raise ValueError("Searx API returned an error: ", response.text)
                result = SearxResults(await response.text())
                self._result = result

        return result

    def run(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> str:
        """Run query through Searx API and parse results.

        You can pass any other params to the searx query API.

        Args:
            query: The query to search for.
            query_suffix: Extra suffix appended to the query.
            engines: List of engines to use for the query.
            categories: List of categories to use for the query.
            **kwargs: extra parameters to pass to the searx API.

        Returns:
            str: The result of the query.

        Raises:
            ValueError: If an error occured with the query.


        Example:
            This will make a query to the qwant engine:

            .. code-block:: python

                from chatgpt-tool-hub.tools.searxng_search.wrapper import SearxSearchWrapper
                searx = SearxSearchWrapper(searxng_search_host="http://my.searx.host")
                searx.run("what is the weather in France ?", engine="qwant")

                # the same result can be achieved using the `!` syntax of searx
                # to select the engine using `query_suffix`
                searx.run("what is the weather in France ?", query_suffix="!qwant")
        """
        if self.searxng_search_output_type == OutputType.JSON:
            return self.to_json(query, engines, categories, query_suffix, **kwargs)
        _params = {
            "q": query,
        }
        params = {**self.params, **_params, **kwargs}

        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += f" {self.query_suffix}"

        if isinstance(query_suffix, str) and len(query_suffix) > 0:
            params["q"] += f" {query_suffix}"

        if isinstance(engines, list) and len(engines) > 0:
            params["engines"] = ",".join(engines)

        if isinstance(categories, list) and len(categories) > 0:
            params["categories"] = ",".join(categories)

        res = self._searx_api_query(params)
        if len(res.answers) > 0:
            return res.answers[0]

        if len(res.results) > 0:
            LOG.debug(f"[searxng-search] output: {res.results}")

            _contents = []
            for idx, result in enumerate(res.results[: self.searxng_search_top_k_results]):
                _header = f"《{filter_text(result.get('title', ''))}》"
                _body = f"{filter_text(result.get('content', ''))}"
                _link = f"{result.get('url', '')}"
                _contents.append(f"{_header}\n{_body}\n[{_link}]\n\n---\n")
            return "\n".join(_contents)

        return "No good search result found"

    async def arun(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> str:
        """Asynchronously version of `run`."""
        raise RuntimeError("implement me!")
        _params = {
            "q": query,
        }
        params = {**self.params, **_params, **kwargs}

        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += f" {self.query_suffix}"

        if isinstance(query_suffix, str) and len(query_suffix) > 0:
            params["q"] += f" {query_suffix}"

        if isinstance(engines, list) and len(engines) > 0:
            params["engines"] = ",".join(engines)

        res = await self._asearx_api_query(params)

        if len(res.answers) > 0:
            return res.answers[0]

        elif len(res.results) > 0:
            return "\n\n".join(
                [r.get("content", "") for r in res.results[: self.searxng_search_top_k_results]]
            )
        else:
            return "No good search result found"

    def to_json(
        self,
        query: str,
        num_results: int,
        engines: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> List[Dict]:
        """Run query through Searx API and returns the results with metadata.

        Args:
            query: The query to search for.

            query_suffix: Extra suffix appended to the query.

            num_results: Limit the number of results to return.

            engines: List of engines to use for the query.

            categories: List of categories to use for the query.

            **kwargs: extra parameters to pass to the searx API.

        Returns:
            Dict with the following keys:

            {
                snippet:  The description of the result.

                title:  The title of the result.

                link: The link to the result.

                engines: The engines used for the result.

                category: Searx category of the result.
            }


        """
        _params = {
            "q": query,
        }
        params = {**self.params, **_params, **kwargs}
        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += f" {self.query_suffix}"
        if isinstance(query_suffix, str) and len(query_suffix) > 0:
            params["q"] += f" {query_suffix}"
        if isinstance(engines, list) and len(engines) > 0:
            params["engines"] = ",".join(engines)
        if isinstance(categories, list) and len(categories) > 0:
            params["categories"] = ",".join(categories)
        results = self._searx_api_query(params).results[:num_results]
        if len(results) == 0:
            return [{"Result": "No good Search Result was found"}]
        LOG.debug(f"[searxng-search] output: {results}")
        return [
            {
                "snippet": result.get("content", ""),
                "title": result["title"],
                "link": result["url"],
                "engines": result["engines"],
                "category": result["category"],
            }
            for result in results
        ]

    async def ato_json(
        self,
        query: str,
        num_results: int,
        engines: Optional[List[str]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> List[Dict]:
        """Asynchronously query with json results.

        Uses aiohttp. See `results` for more info.
        """
        raise RuntimeError("implement me!")
        _params = {
            "q": query,
        }
        params = {**self.params, **_params, **kwargs}

        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += f" {self.query_suffix}"
        if isinstance(query_suffix, str) and len(query_suffix) > 0:
            params["q"] += f" {query_suffix}"
        if isinstance(engines, list) and len(engines) > 0:
            params["engines"] = ",".join(engines)
        results = (await self._asearx_api_query(params)).results[:num_results]
        if len(results) == 0:
            return [{"Result": "No good Search Result was found"}]

        return [
            {
                "snippet": result.get("content", ""),
                "title": result["title"],
                "link": result["url"],
                "engines": result["engines"],
                "category": result["category"],
            }
            for result in results
        ]