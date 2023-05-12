"""Chain that takes in an input and produces an action and action input."""
from __future__ import annotations

import json
import os
import tempfile
from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import yaml
from pydantic import BaseModel, root_validator, validator
from rich.console import Console

from chatgpt_tool_hub.chains import LLMChain
from chatgpt_tool_hub.common.calculate_token import count_string_tokens
from chatgpt_tool_hub.common.callbacks import BaseCallbackManager
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.schema import BotAction, BotFinish, BaseMessage
from chatgpt_tool_hub.models import ALL_MAX_TOKENS_NUM, BOT_SCRATCHPAD_MAX_TOKENS_NUM
from chatgpt_tool_hub.models.base import BaseLLM
from chatgpt_tool_hub.prompts import BasePromptTemplate
from chatgpt_tool_hub.prompts import PromptTemplate
from chatgpt_tool_hub.tools import SummaryTool
from chatgpt_tool_hub.tools.base_tool import BaseTool


class Bot(BaseModel):
    """Class responsible for calling the language model and deciding the action.

    This is driven by an LLMChain. The prompt in the LLMChain MUST include
    a variable called "bot_scratchpad" where the bot can put its
    intermediary work.
    """

    llm_chain: LLMChain
    allowed_tools: Optional[List[str]] = None
    return_values: List[str] = ["output"]
    # 当bot未按要求回复时，最多重试次数
    max_parse_retry_num: int = 1
    max_token_num: int = ALL_MAX_TOKENS_NUM

    console: Console = None

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    @validator("console")
    def set_console(cls, console: Console) -> Console:
        return console or Console()

    @abstractmethod
    def _extract_tool_and_input(self, text: str) -> Optional[Tuple[str, str]]:
        """Extract tool and tool input from llm output."""

    def _fix_text(self, text: str) -> str:
        """Fix the text."""
        raise ValueError("fix_text not implemented for this bot.")

    @property
    def _stop(self) -> List[str]:
        return [
            f"\n{self.observation_prefix.rstrip()}",
            f"\n\t{self.observation_prefix.rstrip()}",
        ]

    def _construct_scratchpad(
        self, intermediate_steps: List[Tuple[BotAction, str]]
    ) -> Union[str, List[BaseMessage]]:
        """Construct the scratchpad that lets the bot continue its thought process."""
        thoughts = ""
        # todo 区分当前对话和历史对话的scratchpad描述
        for action, observation in intermediate_steps:
            thoughts += f"previous constructed JSON: {action.log}\n"
            thoughts += f"{action.tool} tool was called and it returned: {observation}\n\n"
        return thoughts

    def _crop_full_input(self, inputs: str) -> str:
        """ crop too long text """
        if not inputs:
            return inputs
        _input = inputs

        while count_string_tokens(_input) >= BOT_SCRATCHPAD_MAX_TOKENS_NUM:

            # compress text size
            temp_file = tempfile.mkstemp()
            file_path = temp_file[1]

            with open(file_path, "w") as f:
                f.write(_input + "\n")
            # 总结
            _input = SummaryTool(self.console, max_segment_length=2000).run(f"{str(file_path)}, 0")
            try:
                os.remove(file_path)
            except Exception as e:
                LOG.debug(f"remove {file_path} failed... error_info: {repr(e)}")

        return _input

    def _get_next_action(self, full_inputs: Dict[str, str]) -> BotAction:
        full_output = self.llm_chain.predict(**full_inputs)
        parsed_output = self._extract_tool_and_input(full_output)

        action_input = "None" if parsed_output is None else parsed_output[1]
        LOG.info(f"输入: {action_input}")
        retry_num = 0
        while parsed_output is None:
            retry_num += 1
            if retry_num > self.max_parse_retry_num:
                raise ValueError(f"Could not parse LLM output: `{parsed_output}`")

            full_output = self._fix_text(full_output)
            full_inputs["bot_scratchpad"] += full_output
            output = self.llm_chain.predict(**full_inputs)
            # LOG.debug("(fix_text): retry response: " + str(output))
            parsed_output = self._extract_tool_and_input(output)
        return BotAction(
            tool=parsed_output[0], tool_input=parsed_output[1], log=full_output
        )

    def plan(
        self, intermediate_steps: List[Tuple[BotAction, str]], **kwargs: Any
    ) -> Union[BotAction, BotFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        full_inputs = self.get_full_inputs(intermediate_steps, **kwargs)
        action = self._get_next_action(full_inputs)
        if action.tool == self.finish_tool_name:
            return BotFinish({"output": action.tool_input}, action.log)
        return action

    def get_full_inputs(
        self, intermediate_steps: List[Tuple[BotAction, str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """Create the full inputs for the LLMChain from intermediate steps."""
        thoughts = self._construct_scratchpad(intermediate_steps)
        new_inputs = {"bot_scratchpad": self._crop_full_input(thoughts), "stop": self._stop}
        return {**kwargs, **new_inputs}

    def prepare_for_new_call(self) -> None:
        """Prepare the bot for new call, if needed."""
        pass

    @property
    def finish_tool_name(self) -> str:
        """Name of the tool to use to finish the chain."""
        return "Final Answer"

    @property
    def input_keys(self) -> List[str]:
        """Return the input keys.

        :meta private:
        """
        return list(set(self.llm_chain.input_keys) - {"bot_scratchpad"})

    @root_validator(allow_reuse=True)
    def validate_prompt(cls, values: Dict) -> Dict:
        """Validate that prompt matches format."""
        prompt = values["llm_chain"].prompt
        if "bot_scratchpad" not in prompt.input_variables:
            LOG.warning(
                "`bot_scratchpad` should be a variable in prompt.input_variables."
                " Did not find it, so adding it at the end."
            )
            prompt.input_variables.append("bot_scratchpad")
            if isinstance(prompt, PromptTemplate):
                prompt.template += "\n{bot_scratchpad}"
            else:
                raise ValueError(f"Got unexpected prompt type {type(prompt)}")
        return values

    @property
    @abstractmethod
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""

    @property
    @abstractmethod
    def llm_prefix(self) -> str:
        """Prefix to append the LLM call with."""

    @classmethod
    @abstractmethod
    def create_prompt(cls, tools: Sequence[BaseTool]) -> BasePromptTemplate:
        """Create a prompt for this class."""

    @classmethod
    def _validate_tools(cls, tools: Sequence[BaseTool]) -> None:
        """Validate that appropriate tools are passed in."""
        pass

    @classmethod
    def from_llm_and_tools(
        cls,
        llm: BaseLLM,
        tools: Sequence[BaseTool],
        console: Console = Console(),
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ) -> Bot:
        """Construct an bot from an LLM and tools."""
        cls._validate_tools(tools)
        llm_chain = LLMChain(
            llm=llm,
            prompt=cls.create_prompt(tools),
            callback_manager=callback_manager,
        )
        tool_names = [tool.name for tool in tools]
        return cls(llm_chain=llm_chain, console=console, allowed_tools=tool_names, **kwargs)

    def return_stopped_response(
        self,
        early_stopping_method: str,
        intermediate_steps: List[Tuple[BotAction, str]],
        max_iterations: int,
        **kwargs: Any,
    ) -> BotFinish:
        """Return response when bot has been stopped due to max iterations."""
        if early_stopping_method == "force":
            # `force` just returns a constant string
            return BotFinish({"output": "Bot stopped due to max iterations."}, "")
        elif early_stopping_method == "generate":
            # Adding to the previous steps, we now tell the LLM to make a final pred
            thoughts = self._construct_scratchpad(intermediate_steps)
            thoughts += (
                f"你超过了tool使用次数限制: 最多{max_iterations}次。"
                "你现在需要总结当前你了解到的所有信息，来反馈给人类，本次你必须使用answer-user工具!"
                "你需要生成一个final answer:"
            )

            new_inputs = {"bot_scratchpad": self._crop_full_input(thoughts), "stop": self._stop}
            full_inputs = {**kwargs, **new_inputs}
            full_output = self.llm_chain.predict(**full_inputs)
            # We try to extract a final answer
            action, action_input = self._extract_tool_and_input(full_output)

            if action:
                return (
                    BotFinish({"output": action_input}, full_output)
                    if action.lower() in ['answer-user']
                    else BotFinish({"output": "受think_depth限制，系统强制终止了LLM-OS"}, full_output)
                )
            else:
                # If we cannot extract, we just return the full output
                return BotFinish({"output": full_output}, full_output)

        else:
            raise ValueError(
                "early_stopping_method should be one of `force` or `generate`, "
                f"got {early_stopping_method}"
            )

    @property
    @abstractmethod
    def _bot_type(self) -> str:
        """Return Identifier of bot type."""

    def dict(self, **kwargs: Any) -> Dict:
        """Return dictionary representation of bot."""
        _dict = super().dict()
        _dict["_type"] = self._bot_type
        return _dict

    def save(self, file_path: Union[Path, str]) -> None:
        """Save the bot.

        Args:
            file_path: Path to file to save the bot to.

        Example:
        .. code-block:: python

            # If working with bot executor
            bot.bot.save(file_path="path/bot.yaml")
        """
        # Convert file to Path object.
        save_path = Path(file_path) if isinstance(file_path, str) else file_path
        directory_path = save_path.parent
        directory_path.mkdir(parents=True, exist_ok=True)

        # Fetch dictionary to save
        bot_dict = self.dict()

        if save_path.suffix == ".json":
            with open(file_path, "w") as f:
                json.dump(bot_dict, f, indent=4)
        elif save_path.suffix == ".yaml":
            with open(file_path, "w") as f:
                yaml.dump(bot_dict, f, default_flow_style=False)
        else:
            raise ValueError(f"{save_path} must be json or yaml")

    async def aplan(
        self, intermediate_steps: List[Tuple[BotAction, str]], **kwargs: Any
    ) -> Union[BotAction, BotFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        full_inputs = self.get_full_inputs(intermediate_steps, **kwargs)
        action = await self._aget_next_action(full_inputs)
        if action.tool == self.finish_tool_name:
            return BotFinish({"output": action.tool_input}, action.log)
        return action

    async def _aget_next_action(self, full_inputs: Dict[str, str]) -> BotAction:
        full_output = await self.llm_chain.apredict(**full_inputs)
        parsed_output = self._extract_tool_and_input(full_output)
        retry_num = 0
        while parsed_output is None:
            retry_num += 1
            if retry_num > self.max_parse_retry_num:
                raise ValueError(f"Could not parse LLM output: `{parsed_output}`")

            full_output = self._fix_text(full_output)
            full_inputs["bot_scratchpad"] += full_output
            output = await self.llm_chain.apredict(**full_inputs)
            full_output += output
            parsed_output = self._extract_tool_and_input(full_output)
        return BotAction(
            tool=parsed_output[0], tool_input=parsed_output[1], log=full_output
        )
