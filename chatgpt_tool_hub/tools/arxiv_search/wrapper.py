import json
from typing import Any, Dict

from pydantic import BaseModel, Extra, root_validator


class ArxivAPIWrapper(BaseModel):
    """Wrapper around ArvixAPI.

    To use, you should have the ``arxiv`` python package installed.
    This wrapper will use the Arxiv API to conduct searches and
    fetch page summaries. By default, it will return the page summaries
    of the top-k results of an input search.
    """
    arxiv_client: Any
    top_k_results: int = 3

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
        except ImportError:
            raise ValueError(
                "Could not import arxiv python package. "
                "Please it install it with `pip install arxiv`."
            )
        return values

    def run(self, query_json_str: str) -> str:
        import arxiv

        query_json = json.loads(query_json_str)

        search_query = query_json.get("search_query", "")
        max_results = query_json.get("max_results", self.top_k_results)
        sort_by = query_json.get("sort_by", "relevance")
        sort_order = query_json.get("sort_order", "descending")

        # todo avoid it in future
        query = search_query.replace("'", "").replace("\"", "").replace("+", " ")

        if sort_by == "lastUpdatedDate":
            sort_by_input = arxiv.SortCriterion.LastUpdatedDate
        elif sort_by == "submittedDate":
            sort_by_input = arxiv.SortCriterion.SubmittedDate
        else:
            sort_by_input = arxiv.SortCriterion.Relevance

        if sort_order == "ascending":
            sort_order_input = arxiv.SortOrder.Ascending
        else:
            sort_order_input = arxiv.SortOrder.Descending

        search = arxiv.Search(query=query,
                              max_results=max_results,
                              sort_by=sort_by_input,
                              sort_order=sort_order_input)

        _content = ""
        for idx, result in enumerate(self.arxiv_client.results(search)):
            # 标题、作者、published、总结、primary_category、comment、pdf_url
            _content += f"\n第{idx+1}篇：{repr(result.title)}\n"
            _content += f"作者: {[author.name for author in result.authors]}\n"
            try:
                _content += f"发布时间: {result.published.strftime('%Y-%m-%d %H:%M:%S')}\n"
            except Exception as e:
                _content += f"发布时间: None\n"
            _content += f"摘要: {result.summary}\n"
            _content += f"分类: {result.primary_category}\n"
            if result.comment:
                _content += f"备注: {repr(result.comment)}\n"
            _content += f"pdf: {result.pdf_url}\n"
            _content += "\n---\n"
        return _content
