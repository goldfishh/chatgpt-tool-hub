"""Util that calls Wikipedia."""
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Extra, root_validator

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env


class WikipediaAPIWrapper(BaseModel):
    """Wrapper around WikipediaAPI.

    To use, you should have the ``wikipedia`` python package installed.
    This wrapper will use the Wikipedia API to conduct searches and
    fetch page summaries. By default, it will return the page summaries
    of the top-k results of an input search.
    """

    wiki_client: Any  #: :meta private:
    top_k_results: int = 2

    class Config:
        """Configuration for this pydantic object."""
        extra = Extra.ignore

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the python package exists in environment."""
        try:
            import wikipedia
            # 本土化
            wikipedia.set_lang("zh")

            values["top_k_results"] = get_from_dict_or_env(
                values, 'top_k_results', "TOP_K_RESULTS", 2
            )
            values["wiki_client"] = wikipedia
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
        for i in range(min(self.top_k_results, len(search_results))):
            retry_num = 0
            while retry_num <= 1:
                summary = self.fetch_formatted_page_summary(search_results[i])
                if summary is not None:
                    summaries.append(summary)
                    break
                else:
                    # wikipedia api 限制
                    time.sleep(2)
                    retry_num += 1
        _content = "\n\n".join(summaries)
        LOG.debug(f"[wikipedia]: {_content}")
        return _content

    def fetch_formatted_page_summary(self, page: str) -> Optional[str]:
        try:
            wiki_page = self.wiki_client.page(title=page, auto_suggest=False)
            return f"Page: {page}\nSummary: {wiki_page.summary}"
        except Exception as e:
            LOG.info(f"[wikipedia]: {repr(e)}")
            return None
