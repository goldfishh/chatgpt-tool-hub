from typing import Any
from rich.console import Console

from ...chains import LLMChain
from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...prompts import PromptTemplate
from ..tool_register import main_tool_register
from .api_prompt import ARXIV_PROMPT
from .wrapper import ArxivAPIWrapper
from .. import BaseTool

default_tool_name = "arxiv"


class ArxivTool(BaseTool):
    """ a tool to call arxiv api """
    name: str = default_tool_name
    description: str = (
        "Useful for when you need to answer questions about scientific research or search for papers "
        "Like: which papers has a certain author published? "
        "Input should be the title or abstract keywords or author names of a paper you want to search. "
    )
    api_wrapper: ArxivAPIWrapper = None
    debug: bool = False

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console, return_direct=True)
        self.api_wrapper = ArxivAPIWrapper(**tool_kwargs)

        self.debug = get_from_dict_or_env(tool_kwargs, "arxiv_debug", "ARXIV_DEBUG", False)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=PromptTemplate(
            input_variables=["input"],
            template=ARXIV_PROMPT,
        ))

    def _run(self, query: str) -> str:
        """Use the Arxiv tool."""

        _llm_response = self.bot.run(query)
        LOG.debug(f"[arxiv]: search_query: {_llm_response}")

        if self.debug:
            return _llm_response

        _api_response = self.api_wrapper.run(_llm_response)

        return _api_response

    async def _arun(self, query: str) -> str:
        """Use the Arxiv tool asynchronously."""
        raise NotImplementedError("ArxivTool does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: ArxivTool(console, **kwargs), [])


if __name__ == "__main__":
    tool = ArxivTool()
    content = tool.run("帮我找找吴恩达写的论文")
    print(content)
