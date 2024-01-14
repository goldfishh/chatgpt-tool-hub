"""Util that calls Wikipedia."""
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, model_validator

from ...common.log import LOG
from ...common.utils import get_from_dict_or_env



class WikipediaAPIWrapper(BaseModel):
    """Wrapper around WikipediaAPI.

    To use, you should have the ``wikipedia`` python package installed.
    This wrapper will use the Wikipedia API to conduct searches and
    fetch page summaries. By default, it will return the page summaries
    of the top-k results of an input search.
    """

    wiki_client: Any  #: :meta private:
    wikipedia_top_k_results: Optional[int]
    max_retry_num: int = 3

    class Config:
        """Configuration for this pydantic object."""
        extra = 'ignore'

    @model_validator(mode='before')
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the python package exists in environment."""
        proxy = get_from_dict_or_env(values, 'proxy', "PROXY", "")
        proxies = {
            'http': proxy,
            'https': proxy,
        }
        try:
            import wikipedia
            if proxy:
                def _wiki_request(params):
                    '''
                    Make a request to the Wikipedia API using the given search parameters.
                    Returns a parsed dict of the JSON response.
                    '''
                    import requests
                    from datetime import datetime

                    params['format'] = 'json'
                    if not 'action' in params:
                        params['action'] = 'query'

                    headers = {
                        'User-Agent': wikipedia.USER_AGENT
                    }

                    if wikipedia.RATE_LIMIT and wikipedia.RATE_LIMIT_LAST_CALL and \
                        wikipedia.RATE_LIMIT_LAST_CALL + wikipedia.RATE_LIMIT_MIN_WAIT > datetime.now():

                        # it hasn't been long enough since the last API call
                        # so wait until we're in the clear to make the request

                        wait_time = (wikipedia.RATE_LIMIT_LAST_CALL + wikipedia.RATE_LIMIT_MIN_WAIT) - datetime.now()
                        time.sleep(int(wait_time.total_seconds()))

                    r = requests.get(wikipedia.API_URL, params=params, headers=headers, proxies=proxies)

                    if wikipedia.RATE_LIMIT:
                        wikipedia.RATE_LIMIT_LAST_CALL = datetime.now()

                    return r.json()
                wikipedia._wiki_request = _wiki_request
            # 本土化
            wikipedia.set_lang("zh")
            values["wiki_client"] = wikipedia

            values["wikipedia_top_k_results"] = get_from_dict_or_env(
                values, 'wikipedia_top_k_results', "WIKIPEDIA_TOP_K_RESULTS", 2
            )
        except ImportError:
            raise ValueError(
                "Could not import wikipedia python package. "
                "Please it install it with `pip install wikipedia`."
            )

        return values

    def run(self, query: str) -> str:
        """Run Wikipedia search and get page summaries."""
        search_results = self.wiki_client.search(query)
        summaries = []
        for i in range(min(self.wikipedia_top_k_results, len(search_results))):
            retry_num = 0
            while retry_num <= self.max_retry_num:
                summary = self.fetch_formatted_page_summary(search_results[i])
                if summary is not None:
                    summaries.append(summary)
                    time.sleep(1)
                    break
                else:
                    # wikipedia api 限制
                    time.sleep(1)
                    retry_num += 1
        _content = "\n---\n".join(summaries)
        LOG.debug(f"[wikipedia] output: \n{_content}")
        return _content

    def fetch_formatted_page_summary(self, page: str) -> Optional[str]:
        from wikipedia.exceptions import DisambiguationError
        try:
            wiki_page = self.wiki_client.page(title=page, auto_suggest=True)
            return f"Page: {page}\nSummary: {wiki_page.summary}"
        except DisambiguationError as e:
            LOG.debug(f"[wikipedia] catch DisambiguationError, igrore it...")
        except Exception as e:
            LOG.info(f"[wikipedia] error: \n{repr(e)}")
        return None
