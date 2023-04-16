import asyncio
import os
from typing import Any, List

from chatgpt_tool_hub.chains.llm import LLMChain
from chatgpt_tool_hub.common.calculate_token import num_tokens_from_messages as get_token_num
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.models import build_model_params
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.summary import MAP_PROMPT, REDUCE_PROMPT


class TextClipper:

    def __init__(self, max_segment_length=3000, seperator="\n"):
        self.max_segment_length = max_segment_length
        self.seperator = seperator

    def _clip_single_long_text(self, text: str) -> List[str]:
        _token_num = get_token_num(text)
        if _token_num <= self.max_segment_length:
            return [text]

        _cut_step = int(len(text) * self.max_segment_length / _token_num)
        _cut_index = list(range(0, len(text), _cut_step))
        # add index to stop
        _cut_index.append(len(text))

        _iter = 0
        clip_list = []
        while _iter < len(_cut_index) - 1:
            # todo: some words or sentences may be split in _cut_index
            _clip_text = text[_cut_index[_iter]:_cut_index[_iter+1]]
            _cut_token_num = get_token_num(_clip_text)
            if _cut_token_num <= self.max_segment_length:
                clip_list.append(_clip_text)
            _iter += 1
        return clip_list

    def clip(self, text: str, capacity: int) -> List[str]:
        if get_token_num(text) <= self.max_segment_length:
            return [text]
        if capacity < 0:
            capacity = 0
        segments = text.split(self.seperator)
        segments = list(filter(lambda x: x.strip() != "", segments))
        _segment_num = len(segments)

        clip_list = []
        segment_cache = ""

        now_ctn, total_ctn = 0, 0
        for iter in reversed(range(_segment_num)):
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
                if total_ctn >= capacity:
                    # early stop
                    segment_cache = ""
                    break
                segment_cache = segments[iter]
                now_ctn = 1
            else:
                segment_cache += _mix_text
                now_ctn += 1
        if segment_cache:
            clip_list.extend(self._clip_single_long_text(segment_cache))
        return clip_list


default_tool_name = "summary"


class SummaryTool(BaseTool):

    name = default_tool_name
    description = "input file_path, summary_num"

    message_num: int = 50
    max_segment_length: int = 3000

    map_bot: Any = None
    reduce_bot: Any = None

    def __init__(self, **tool_kwargs: Any):
        super().__init__()
        self.message_num = get_from_dict_or_env(tool_kwargs, "message_num", "MESSAGE_NUM", 100)
        self.max_segment_length = get_from_dict_or_env(tool_kwargs, "max_segment_length", "MAX_SEGMENT_LENGTH", 3000)
        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))

        self.map_bot = LLMChain(llm=llm, prompt=MAP_PROMPT)
        self.reduce_bot = LLMChain(llm=llm, prompt=REDUCE_PROMPT)

    async def _amap(self, clip_text_list: List[str]):
        tasks = []
        for text in clip_text_list:
            resp = await self.map_bot.arun(text=text)
            tasks.append(resp)
        map_text_list = await asyncio.gather(*tasks)
        return map_text_list

    def _run(self, tool_input: str) -> str:
        """run the tool"""
        try:
            file_path, summary_num = tool_input.split(",", 1)
        except Exception as e:
            LOG.error(e)
            return "failing in parsing the input of SummaryTool, " \
                   "you should use a comma to split file_path and summary_num"

        if not os.path.exists(file_path):
            return f"no file in path: {file_path}, please double-check you file path is valid"

        try:
            self.summary_num = int(summary_num)
        except Exception as e:
            LOG.error(e)

        with open(tool_input, "r") as f:
            source_text = f.read()
            _clipper = TextClipper(self.max_segment_length)
            _clip_text_list = _clipper.clip(source_text, self.message_num)



            map_text = _clipper.seperator.join(map_text_list)
            reduce_text = self.reduce_bot.run(text=map_text)
            # todo reduce_text token_num > max_segment_length
            return reduce_text

    async def _arun(self, file_path: str) -> str:
        """use this tool async."""
        raise NotImplementedError("summary tool not support async yet")


if __name__ == "__main__":
    tool = SummaryTool()
    content = tool.run("/Users/goldfish/Desktop/chat.log, 200")
    print(content)
