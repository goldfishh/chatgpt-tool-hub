import asyncio
import os
from typing import Any, List

from rich.console import Console
from rich.panel import Panel

from chatgpt_tool_hub.chains.llm import LLMChain
from chatgpt_tool_hub.common.calculate_token import count_string_tokens as get_token_num
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.models import build_model_params
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.summary import MAP_PROMPT, REDUCE_PROMPT


class TextClipper:

    def __init__(self, max_segment_length=2500, seperator="\n"):
        self.max_segment_length = max_segment_length
        self.seperator = seperator

    def _clip_single_long_text(self, text: str) -> List[str]:
        _token_num = get_token_num(text)
        if _token_num <= self.max_segment_length:
            return [text]

        _cut_step = min(int(len(text) * self.max_segment_length / _token_num), self.max_segment_length)
        _cut_index = list(range(0, len(text), _cut_step))
        # add index to stop
        _cut_index.append(len(text))

        _iter = 0
        clip_list = []
        while _iter < len(_cut_index) - 1:
            # todo: some words or sentences may be split in two parts
            _clip_text = text[_cut_index[_iter]:_cut_index[_iter + 1]]
            _cut_token_num = get_token_num(_clip_text)
            if _cut_token_num <= self.max_segment_length:
                clip_list.append(_clip_text)
            _iter += 1
        return clip_list

    def clip(self, text: str, capacity: int = 0) -> List[str]:
        if get_token_num(text) <= self.max_segment_length:
            return [text]
        capacity = max(capacity, 0)
        segments = text.split(self.seperator)
        segments = list(filter(lambda x: x.strip() != "", segments))
        _segment_num = len(segments)

        clip_list = []
        segment_cache = ""

        now_ctn, total_ctn = 0, 0
        for iter in range(_segment_num):
            _mix_text = self.seperator.join([segment_cache, segments[iter]])
            _token_num_of_mix = get_token_num(_mix_text)
            if _token_num_of_mix > self.max_segment_length:
                # 长文本
                if now_ctn == 1:
                    clip_list.extend(self._clip_single_long_text(segment_cache))
                elif now_ctn > 1:
                    clip_list.append(segment_cache)
                total_ctn += now_ctn
                # not precise here
                if capacity != 0 and total_ctn >= capacity:
                    # early stop
                    segment_cache = ""
                    break
                segment_cache = segments[iter]
                now_ctn = 1
            else:
                segment_cache = _mix_text
                now_ctn += 1
        if segment_cache:
            clip_list.extend(self._clip_single_long_text(segment_cache))
        return clip_list


default_tool_name = "summary"


class SummaryTool(BaseTool):
    name = default_tool_name
    description = (
        "Useful when you want to summarize the content of a file. "
        "The input is a comma-separated of file_path and a number. "
        "The number represents summarizing only the first N lines of the file, "
        "and when the number is 0, it means summarizing the entire file. "
        "If you don't know what the file path is, you cannot use this tool."
    )

    message_num: int = 100
    max_segment_length: int = 2500

    map_bot: Any = None
    reduce_bot: Any = None

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)
        tool_kwargs = {} if tool_kwargs is None else tool_kwargs
        self.message_num = get_from_dict_or_env(tool_kwargs, "message_num", "MESSAGE_NUM", 100)
        self.max_segment_length = get_from_dict_or_env(tool_kwargs, "max_segment_length", "MAX_SEGMENT_LENGTH", 2500)
        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))

        self.map_bot = LLMChain(llm=llm, prompt=MAP_PROMPT)
        self.reduce_bot = LLMChain(llm=llm, prompt=REDUCE_PROMPT)

    async def _acall(self, bot: LLMChain, clip_text_list: List[str]):
        tasks = []
        for text in clip_text_list:
            task = asyncio.create_task(bot.arun(text=text))
            tasks.append(task)
        return await asyncio.gather(*tasks)

    def _run(self, tool_input: str) -> str:
        """run the tool"""
        try:
            file_path, message_num = tool_input.split(",", 1)
        except Exception as e:
            LOG.error("[summary] failing in parsing the input of SummaryTool, "
                      "you should use a comma to split file_path and message_num"
                      f"input: {tool_input}, error: {repr(e)}")
            file_path = tool_input
            message_num = self.message_num

        if not os.path.isfile(file_path.split(",")[0]):
            return f"no file in path: {file_path}, please double-check you file path is valid"

        try:
            self.message_num = int(message_num)
        except Exception as e:
            LOG.error(repr(e))

        _clipper = TextClipper(self.max_segment_length)
        with open(file_path, "r") as f:
            source_text = f.read()

        _text = source_text
        ctn = 0
        while get_token_num(_text) >= self.max_segment_length:
            ctn += 1
            if ctn > 8:
                LOG.warning(f"[summary] 我已经map-reduce {ctn}轮了，但是文本量还是很长，避免死循环我帮你关掉了~")
            # map
            _clip_text_list = _clipper.clip(_text, self.message_num)
            # async call llm to get summary of each clip_text
            map_text_list = asyncio.run(self._acall(self.map_bot, _clip_text_list))
            map_text = _clipper.seperator.join(map_text_list)

            LOG.debug(f"[summary] round:{ctn}, map_list: {map_text}")
            # reduce
            _clip_summary_list = _clipper.clip(map_text, self.message_num)

            reduce_text_list = asyncio.run(self._acall(self.reduce_bot, _clip_summary_list))
            reduce_text = _clipper.seperator.join(reduce_text_list)
            LOG.debug(f"[summary] round:{ctn}, reduce_list: {reduce_text}")
            _text = reduce_text

            self.console.print(Panel(f"{_text}",
                                     title=f"[bright_magenta]Summary tool[/] 第{ctn}轮总结",
                                     highlight=True))
            
        if ctn > 2:
            self.console.print(Panel(f"{_text}",
                                     title=f"[bright_magenta]Summary tool[/] 最终总结",
                                     highlight=True))
            
        return _text

    async def _arun(self, file_path: str) -> str:
        """use this tool async."""
        raise NotImplementedError("summary tool not support async yet")


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: SummaryTool(console, **kwargs), [])

if __name__ == "__main__":
    tool = SummaryTool(**{})
    content = tool.run("/Users/goldfish/Desktop/finance.log, 1000")
    print(content)
