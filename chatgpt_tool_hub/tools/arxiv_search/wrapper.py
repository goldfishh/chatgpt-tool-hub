import json
from typing import Any, Dict
from enum import Enum
from pydantic import BaseModel, Extra, root_validator

from ...common.utils import get_from_dict_or_env
from ...common.log import LOG

class OutputType(str, Enum):
    Text = "text"
    PDF = "pdf"
    ALL = "all"

class SortBy(str, Enum):
    Relevance = "relevance"
    LastUpdatedDate = "lastUpdatedDate"
    SubmittedDate = "submittedDate"

class SortOrder(str, Enum):
    Ascending = "ascending"
    Descending = "descending"

class ArxivAPIWrapper(BaseModel):
    """Wrapper around ArvixAPI.

    To use, you should have the ``arxiv`` python package installed.
    This wrapper will use the Arxiv API to conduct searches and
    fetch page summaries. By default, it will return the page summaries
    of the top-k results of an input search.
    """
    arxiv_client: Any
    max_retry_num: int = 3
    
    arxiv_simple: bool = True
    arxiv_top_k_results: int = 3
    
    arxiv_sort_by: SortBy = SortBy.Relevance
    arxiv_sort_order: SortOrder = SortOrder.Descending
    arxiv_output_type: OutputType = OutputType.Text

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.ignore

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the python package exists in environment."""
        try:
            import arxiv

            values["arxiv_client"] = arxiv.Client(
                page_size=1,
                delay_seconds=3,  # "arXiv's Terms of Use" asks you no more than one request per three seconds
                num_retries=3
            )

            values["arxiv_simple"] = get_from_dict_or_env(values, "arxiv_simple", "ARXIV_SIMPLE", True)
            values["arxiv_top_k_results"] = get_from_dict_or_env(values, "arxiv_top_k_results", "ARXIV_TOP_K_RESULTS", 3)
            
            values["arxiv_sort_by"] = get_from_dict_or_env(values, "arxiv_sort_by", "ARXIV_SORT_BY", SortBy.Relevance)
            values["arxiv_sort_order"] = get_from_dict_or_env(values, "arxiv_max_results", "ARXIV_MAX_RESULTS", SortOrder.Descending)
            values["arxiv_output_type"] = get_from_dict_or_env(values, "arxiv_output_type", "ARXIV_OUTPUT_TYPE",  OutputType.Text)
        except ImportError:
            raise ValueError(
                "Could not import arxiv python package. "
                "Please it install it with `pip install arxiv`."
            )
        return values

    def run(self, query_json_str: str, retry_num: int = 0, **kwargs) -> str:
        import arxiv
        if (retry_num > self.max_retry_num):
            return "exceed max_retry_num"
        
        query_json = json.loads(query_json_str)

        search_query = query_json.get("search_query", "")

        query = search_query.replace("'", "").replace("\"", "").replace("+", " ")

        if self.arxiv_sort_by == "lastUpdatedDate":
            sort_by_input = arxiv.SortCriterion.LastUpdatedDate
        elif self.arxiv_sort_by == "submittedDate":
            sort_by_input = arxiv.SortCriterion.SubmittedDate
        else:
            sort_by_input = arxiv.SortCriterion.Relevance

        if self.arxiv_sort_order == "ascending":
            sort_order_input = arxiv.SortOrder.Ascending
        else:
            sort_order_input = arxiv.SortOrder.Descending

        try:
            search = arxiv.Search(query=query,
                                max_results=self.arxiv_top_k_results,
                                sort_by=sort_by_input,
                                sort_order=sort_order_input)
            _content = ""
            for idx, result in enumerate(self.arxiv_client.results(search)):
                # 标题、作者、published、总结、primary_category、comment、pdf_url
                _content += f"No.{idx+1}:《{str(result.title)}》\n" if not self.arxiv_simple else f"《{str(result.title)}》\n"
                if self.arxiv_output_type in [OutputType.Text, OutputType.ALL]:
                    _content += f"Author: {' '.join([author.name for author in result.authors])}\n"
                    try:
                        _content += f"submitted date: {result.published.strftime('%Y-%m-%d %H:%M:%S')}\n" if not self.arxiv_simple else ""
                    except Exception as e:
                        LOG.exception(e)
                    _content += f"Abstract: {result.summary}\n"
                    if result.primary_category:
                        _content += f"Category: {result.primary_category}\n" if not self.arxiv_simple else ""
                    if result.comment:
                        _content += f"备注: {repr(result.comment)}\n" if not self.arxiv_simple else ""

                if self.arxiv_output_type in [OutputType.PDF, OutputType.ALL]:
                    _content += f"pdf: {result.pdf_url}\n"
                _content += "\n---\n\n"
        except Exception as e:
            # LOG.DEBUG(e)
            return self.run(query_json_str, retry_num+1)
        return _content
