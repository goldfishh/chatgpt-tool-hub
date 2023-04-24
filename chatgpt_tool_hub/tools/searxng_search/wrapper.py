"""Utility for using SearxNG meta search API.

SearxNG is a privacy-friendly free metasearch engine that aggregates results from
`multiple search engines
<https://docs.searxng.org/admin/engines/configured_engines.html>`_ and databases and
supports the `OpenSearch
<https://github.com/dewitt/opensearch/blob/master/opensearch-1-1-draft-6.md>`_
specification.

More detailes on the installtion instructions `here. <../../ecosystem/searx.html>`_

For the search API refer to https://docs.searxng.org/dev/search_api.html

Quick Start
-----------


In order to use this utility you need to provide the searx host. This can be done
by passing the named parameter :attr:`searx_search_host <SearxSearchWrapper.searx_search_host>`
or exporting the environment variable SEARX_SEARCH_HOST.
Note: this is the only required parameter.

Then create a searx search instance like this:

    .. code-block:: python

        from chatgpt-tool-hub.tools.searxng_search.wrapper import SearxSearchWrapper

        # when the host starts with `http` SSL is disabled and the connection
        # is assumed to be on a private network
        searx_search_host='http://self.hosted'

        search = SearxSearchWrapper(searx_search_host=searx_search_host)


You can now use the ``search`` instance to query the searx API.

Searching
---------

Use the :meth:`run() <SearxSearchWrapper.run>` and
:meth:`results() <SearxSearchWrapper.results>` methods to query the searx API.
Other methods are are available for convenience.

:class:`SearxResults` is a convenience wrapper around the raw json result.

Example usage of the ``run`` method to make a search:

    .. code-block:: python

        s.run(query="what is the best search engine?")

Engine Parameters
-----------------

You can pass any `accepted searx search API
<https://docs.searxng.org/dev/search_api.html>`_ parameters to the
:py:class:`SearxSearchWrapper` instance.

In the following example we are using the
:attr:`engines <SearxSearchWrapper.engines>` and the ``language`` parameters:

    .. code-block:: python

        # assuming the searx host is set as above or exported as an env variable
        s = SearxSearchWrapper(engines=['google', 'bing'],
                            language='es')

*NOTE*: A search suffix can be defined on both the instance and the method level.
The resulting query will be the concatenation of the two with the former taking
precedence.


See `SearxNG Configured Engines
<https://docs.searxng.org/admin/engines/configured_engines.html>`_ and
`SearxNG Search Syntax <https://docs.searxng.org/user/index.html#id1>`_
for more details.

Notes
-----
This wrapper is based on the SearxNG fork https://github.com/searxng/searxng which is
better maintained than the original Searx project and offers more features.

Public searxNG instances often use a rate limiter for API usage, so you might want to
use a self hosted instance and disable the rate limiter.

If you are self-hosting an instance you can customize the rate limiter for your
own network as described `here <https://github.com/searxng/searxng/pull/2129>`_.


For a list of public SearxNG instances see https://searx.space/
"""

import json
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Extra, Field, PrivateAttr, root_validator, validator

from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.tools.web_requests import RequestsWrapper


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


class SearxSearchWrapper(BaseModel):
    """Wrapper for Searx API.

    To use you need to provide the searx host by passing the named parameter
    ``searx_search_host`` or exporting the environment variable ``SEARX_SEARCH_HOST``.

    In some situations you might want to disable SSL verification, for example
    if you are running searx locally. You can do this by passing the named parameter
    ``unsecure``. You can also pass the host url scheme as ``http`` to disable SSL.

    Example:
        .. code-block:: python

            from chatgpt-tool-hub.tools.searxng_search.wrapper import SearxSearchWrapper
            searx = SearxSearchWrapper(searx_search_host="http://localhost:8888")

    Example with SSL disabled:
        .. code-block:: python

            from chatgpt-tool-hub.tools.searxng_search.wrapper import SearxSearchWrapper
            # note the unsecure parameter is not needed if you pass the url scheme as
            # http
            searx = SearxSearchWrapper(searx_search_host="http://localhost:8888",
                                                    unsecure=True)


    """

    _result: SearxResults = PrivateAttr()
    searx_search_host: str = ""
    unsecure: bool = False
    params: dict = Field(default_factory=_get_default_params)
    headers: Optional[dict] = None
    engines: Optional[List[str]] = []
    categories: Optional[List[str]] = []
    query_suffix: Optional[str] = ""
    top_k_results: int = 2
    aiosession: Optional[Any] = None

    @validator("unsecure")
    def disable_ssl_warnings(cls, v: bool) -> bool:
        """Disable SSL warnings."""
        if v:
            try:
                import urllib3

                urllib3.disable_warnings()
            except ImportError as e:
                print(e)
        return v

    @root_validator()
    def validate_params(cls, values: Dict) -> Dict:
        """Validate that custom searx params are merged with default ones."""

        values["params"] = {**_get_default_params(), **values["params"]}

        if engines := values.get("engines"):
            values["params"]["engines"] = ",".join(engines)

        if categories := values.get("categories"):
            values["params"]["categories"] = ",".join(categories)

        searx_search_host = get_from_dict_or_env(values, "searx_search_host", "SEARX_SEARCH_HOST")
        if not searx_search_host.startswith("http"):
            print(
                f"Warning: missing the url scheme on host \
                ! assuming secure https://{searx_search_host} "
            )
            searx_search_host = f"https://{searx_search_host}"
        elif searx_search_host.startswith("http://"):
            values["unsecure"] = True
            cls.disable_ssl_warnings(True)
        values["searx_search_host"] = searx_search_host

        values["top_k_results"] = get_from_dict_or_env(
            values, 'top_k_results', "TOP_K_RESULTS", 2
        )

        return values

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.ignore

    def _searx_api_query(self, params: dict) -> SearxResults:
        """Actual request to searx API."""
        requests_wrapper = RequestsWrapper(headers=self.headers)
        raw_result = requests_wrapper.get(self.searx_search_host, params=params,
                                          raise_for_status=True, verify=not self.unsecure)
        # test if http result is ok
        res = SearxResults(raw_result)
        self._result = res
        return res

    async def _asearx_api_query(self, params: dict) -> SearxResults:
        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.searx_search_host,
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
                self.searx_search_host,
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
                searx = SearxSearchWrapper(searx_search_host="http://my.searx.host")
                searx.run("what is the weather in France ?", engine="qwant")

                # the same result can be achieved using the `!` syntax of searx
                # to select the engine using `query_suffix`
                searx.run("what is the weather in France ?", query_suffix="!qwant")
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

        res = self._searx_api_query(params)

        if len(res.answers) > 0:
            return res.answers[0]

        elif len(res.results) > 0:
            return "\n\n".join(
                [r.get("content", "") for r in res.results[: self.top_k_results]]
            )
        else:
            return "No good search result found"

    async def arun(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        query_suffix: Optional[str] = "",
        **kwargs: Any,
    ) -> str:
        """Asynchronously version of `run`."""
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
                [r.get("content", "") for r in res.results[: self.top_k_results]]
            )
        else:
            return "No good search result found"

    def results(
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

    async def aresults(
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