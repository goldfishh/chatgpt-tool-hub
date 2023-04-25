import os
import tempfile
from typing import Any

from rich.console import Console

from chatgpt_tool_hub.chains import LLMChain
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.models import build_model_params
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.prompts import PromptTemplate
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.arxiv_search.api_prompt import ARXIV_PROMPT
from chatgpt_tool_hub.tools.arxiv_search.wrapper import ArxivAPIWrapper
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.summary import SummaryTool

default_tool_name = "arxiv"


class ArxivTool(BaseTool):
    """ a tool to call arxiv api """

    name = default_tool_name
    description = (
        "Useful for when you need to answer questions about scientific research or search for papers "
        "Like: which papers has a certain author published? "
        "Input should be the title or abstract keywords or author names of a paper you want to search. "
    )
    bot: Any = None

    api_wrapper: ArxivAPIWrapper = None

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console, return_direct=True)

        self.api_wrapper = ArxivAPIWrapper(**tool_kwargs)
        self.arxiv_summary = get_from_dict_or_env(tool_kwargs, "arxiv_summary", "ARXIV_SUMMARY", True)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        prompt = PromptTemplate(
            input_variables=["input"],
            template=ARXIV_PROMPT,
        )
        self.bot = LLMChain(llm=llm, prompt=prompt)

    def _run(self, query: str) -> str:
        """Use the Arxiv tool."""

        _llm_response = self.bot.run(query)
        LOG.info(f"[arxiv]: search_query: {_llm_response}")

        _api_response = self.api_wrapper.run(_llm_response)

        if not self.arxiv_summary:
            return _api_response

        temp_file = tempfile.mkstemp()
        file_path = temp_file[1]
        with open(file_path, "w") as f:
            f.write(_api_response + "\n")

        _input = SummaryTool(max_segment_length=2400).run(f"{str(file_path)}, 0")
        try:
            os.remove(file_path)
        except Exception as e:
            LOG.debug(f"remove {file_path} failed... error_info: {repr(e)}")

        return _input

    async def _arun(self, query: str) -> str:
        """Use the Arxiv tool asynchronously."""
        raise NotImplementedError("ArxivTool does not support async")


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: ArxivTool(console, **kwargs), [])


if __name__ == "__main__":
    tool = ArxivTool()
    content = tool.run("帮我找找吴恩达写的论文")
    print(content)
