import os
import asyncio
from typing import Any, List

from rich.console import Console
from rich.panel import Panel

from ...chains.llm import LLMChain
from ...models.calculate_token import count_string_tokens as get_token_num
from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ..tool_register import main_tool_register
from .. import BaseTool
from .prompt import MAP_QUERY_PROMPT, REDUCE_QUERY_PROMPT
from .text_clipper import TextClipper


default_tool_name = "summary"


class SummaryTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "Useful when you want to summarize the content of a file. "
        "The input is a comma-separated of absolute path of the file and a number, like 'fakepath, 0'."
        "The number indicates how many lines to summarize, with 0 meaning the entire file."
        "You must know the file path to use this tool."
    )

    max_segment_length: int = 2500

    map_bot: Any = None
    reduce_bot: Any = None
    clipper: TextClipper = None

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)
        # 总结到多少token停止
        self.max_segment_length = get_from_dict_or_env(tool_kwargs, "summary_max_segment_length", "SUMMARY_MAX_SEGMENT_LENGTH", 2500)
        if self.max_segment_length < 500: self.max_segment_length = 500  # avoid too small
        if self.max_segment_length > 4000: self.max_segment_length = 4000 # upper bound
        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))

        self.map_bot = LLMChain(llm=llm, prompt=MAP_QUERY_PROMPT)
        self.reduce_bot = LLMChain(llm=llm, prompt=REDUCE_QUERY_PROMPT)
        self.clipper = TextClipper(self.max_segment_length)

    async def _acall(self, bot: LLMChain, clip_text_list: List[str]):
        tasks = []
        for text in clip_text_list:
            task = asyncio.create_task(bot.arun(text=text))
            tasks.append(task)
        return await asyncio.gather(*tasks)

    def _summary(self, text: str) -> str:
        ctn = 0
        _text = text
        while get_token_num(_text) >= self.max_segment_length:
            ctn += 1
            if ctn > 3:
                LOG.warning(f"[summary] 我已经map-reduce {ctn}轮了，但是文本量还是很长，避免死循环我帮你关掉了~")
                break
            # map
            _clip_text_list = self.clipper.clip(_text)
            map_text_list = []
            for _clip_text in _clip_text_list:
                map_text_list.append(self.map_bot(_clip_text)["text"])
                # TODO has serious performance issues.
                # asyncio.run(self._acall(self.map_bot, _clip_text_list))

            map_text = self.clipper.seperator.join(map_text_list)
            LOG.debug(f"[summary] round:{ctn}, map_text: \n{map_text}")
            # reduce
            _clip_summary_list = self.clipper.clip(map_text)

            reduce_text_list = []
            for _clip_text in _clip_summary_list:
                reduce_text_list.append(self.reduce_bot(_clip_text)["text"])
            # TODO has serious performance issues.
            # reduce_text_list = asyncio.run(self._acall(self.reduce_bot, _clip_summary_list))
                
            reduce_text = self.clipper.seperator.join(reduce_text_list)
            LOG.debug(f"[summary] round:{ctn}, reduce_text: \n{reduce_text}")
            _text = reduce_text
            if self.console:
                self.console.print(Panel(f"{_text}",
                                        title=f"[bright_magenta]Summary tool[/] 第{ctn}轮总结",
                                        highlight=True))
            
        if self.console and ctn > 2:
            self.console.print(Panel(f"{_text}",
                                    title=f"[bright_magenta]Summary tool[/] 最终总结",
                                        highlight=True))
        return _text

    def path(self, path: str) -> str:
        if not os.path.isfile(path.strip()):
            return f"no file in path: {path}, please double-check you file path is valid"
        
        with open(path, "r") as f:
            source_text = f.read()
        return self._summary(source_text)

    def text(self, text: str) -> str:
        return self._summary(text)

    def _run(self, url: str) -> str:
        """run the tool"""
        from chatgpt_tool_hub.tools.tool_register import main_tool_register
        try:
            _use_tool = "url-get"
            if main_tool_register.get_registered_tool().get('browser'):
                _use_tool = "browser"
            _func, _ = main_tool_register.get_registered_tool()[_use_tool]
            _tool = _func()
            source_text = _tool.run(url.strip())
            return self._summary(source_text)
        except Exception as e:
            LOG.error(repr(e))
            return "[summary] unknown error"

    async def _arun(self, url: str) -> str:
        """use this tool async."""
        raise NotImplementedError("summary tool not support async yet")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: SummaryTool(console, **kwargs), [])

if __name__ == "__main__":
    url = "https://www.wenku8.net/novel/2/2428/148057.htm"
    tool = SummaryTool(summary_max_segment_length=4000)
    result = tool.run(url)
    print(result)
