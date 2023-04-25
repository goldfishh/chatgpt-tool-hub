"""An bot designed to hold a conversation in addition to using tools."""
from __future__ import annotations

import json
import traceback
from typing import Any, List, Optional, Sequence, Tuple, Union, Dict

from rich.console import Console
from rich.panel import Panel
from chatgpt_tool_hub.bots.chat_bot.prompt import FORMAT_INSTRUCTIONS, PREFIX, SUFFIX
from chatgpt_tool_hub.chains import LLMChain
from chatgpt_tool_hub.common import json_utils
from chatgpt_tool_hub.common.callbacks import BaseCallbackManager
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.schema import BotAction, BotFinish
from chatgpt_tool_hub.engine import Bot
from chatgpt_tool_hub.models.base import BaseLLM
from chatgpt_tool_hub.prompts import PromptTemplate
from chatgpt_tool_hub.tools.base_tool import BaseTool

default_ai_prefix = "LLM-OS"
default_human_prefix = "user"


class ChatBot(Bot):
    """An bot designed to hold a conversation in addition to using tools."""

    ai_prefix: str = default_ai_prefix
    human_prefix: str = default_human_prefix

    @property
    def _bot_type(self) -> str:
        """Return Identifier of bot type."""
        return "chat-bot"

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "Observation: "

    def _fix_text(self, text: str) -> str:
        tool_names = ", ".join(list(self.allowed_tools)) if self.allowed_tools else ""
        instruction_text = FORMAT_INSTRUCTIONS.format(
            tool_names=tool_names, human_prefix=self.human_prefix
        )
        return f"\n\nYou just told me: {text}, but it doesn't meet the format I mentioned to you. \n\nformat: {instruction_text}. \n\nYou should understand why you did not input the correct format, correct it and try again. \n\n"

    @property
    def llm_prefix(self) -> str:
        """Prefix to append the llm call with."""
        return "Thought:"

    @classmethod
    def create_prompt(
            cls,
            tools: Sequence[BaseTool],
            prefix: str = PREFIX,
            suffix: str = SUFFIX,
            format_instructions: str = FORMAT_INSTRUCTIONS,
            ai_prefix: str = default_ai_prefix,
            human_prefix: str = default_human_prefix,
            input_variables: Optional[List[str]] = None,
    ) -> PromptTemplate:
        """Create prompt in the style of the zero shot bot.

        Args:
            tools: List of tools the bot will have access to, used to format the
                prompt.
            prefix: String to put before the list of tools.
            suffix: String to put after the list of tools.
            ai_prefix: String to use before AI output.
            human_prefix: String to use before human output.
            input_variables: List of input variables the final prompt will expect.

        Returns:
            A PromptTemplate with the template assembled from the pieces here.
        """
        tool_strings = "\n".join(
            [f"> {tool.name}: {tool.description}" for tool in tools]
        )
        tool_names = ", ".join([tool.name for tool in tools])

        instruction_text = format_instructions.format(human_prefix=human_prefix, tool_names=tool_names)
        prefix = prefix.format(human_prefix=human_prefix)

        template = "\n\n".join([prefix, tool_strings, instruction_text, suffix])
        if input_variables is None:
            input_variables = ["input", "chat_history", "bot_scratchpad"]
        return PromptTemplate(template=template, input_variables=input_variables)

    def plan(
        self, intermediate_steps: List[Tuple[BotAction, str]], **kwargs: Any
    ) -> Union[BotAction, BotFinish]:
        """Given input, decided what to do."""
        full_inputs = self.get_full_inputs(intermediate_steps, **kwargs)
        action = self._get_next_action(full_inputs)
        if action.tool == "answer-user":
            return BotFinish({"output": action.tool_input}, action.log)
        return action

    def get_full_inputs(
        self, intermediate_steps: List[Tuple[BotAction, str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """Create the full inputs for the LLMChain from intermediate steps."""
        thoughts = self._construct_scratchpad(intermediate_steps)
        # todo remove stop
        new_inputs = {"bot_scratchpad": self._crop_full_input(thoughts), "stop": self._stop}
        return {**kwargs, **new_inputs}

    def _get_next_action(self, full_inputs: Dict[str, str]) -> BotAction:
        llm_answer_str = self.llm_chain.predict(**full_inputs)

        action, action_input = self._extract_tool_and_input(llm_answer_str)

        LOG.info(f"输入: {action_input}")
        
        # json 解析错误重试
        retry_num = 0
        while not action:
            retry_num += 1
            if retry_num > self.max_parse_retry_num:
                raise ValueError(f"Could not parse LLM output: `{llm_answer_str}`")

            full_output = self._fix_text(llm_answer_str)
            full_inputs["bot_scratchpad"] += full_output
            output = self.llm_chain.predict(**full_inputs)

            action, action_input = self._extract_tool_and_input(output)

            LOG.info(f"重试输入: {action_input}")
        return BotAction(
            tool=action, tool_input=action_input, log=llm_answer_str
        )

    @property
    def finish_tool_name(self) -> str:
        """Name of the tool to use to finish the chain."""
        return self.ai_prefix

    def _extract_tool_and_input(self, llm_output: str) -> Optional[Tuple[str, str]]:
        # 1. json loads and 修复 & 错误处理
        llm_reply_json = self.parse_reply_json(llm_output)
        action, action_input = "", ""

        try:
            if not isinstance(llm_reply_json, dict):
                return "Error:", f"'response_json' object is not dictionary {llm_reply_json}"

            if "tool" not in llm_reply_json:
                return "Error:", "Missing 'tool' object in JSON"

            tool_dict = llm_reply_json["tool"]
            if not isinstance(tool_dict, dict):
                return "Error:", "'tool' object is not a dictionary"

            if "name" not in tool_dict:
                return "Error:", "Missing 'name' field in 'tool_dict' object"

            action = tool_dict["name"]
            action_input = tool_dict.get("input", "")

        except json.decoder.JSONDecodeError:
            LOG.error("Error:", "Invalid JSON")

        except Exception as e:
            LOG.error(f"Error: {repr(e)}")

        if action.lower() == "answer-user" and action_input in ['', '空', '无']:
            action_input = llm_reply_json.get('thoughts', {}).get('speak', '')

        if action.lower() not in self.allowed_tools:
            return "answer-user", action_input

        if action.lower() != "answer-user":
            self.console.print(f"√ 我在用 [bold cyan]{action}[/] 工具...")

        LOG.info(f"执行Tool: {action}中...")
        return action.strip(), action_input.strip()

    def parse_reply_json(self, assistant_reply) -> dict:
        """Prints the assistant's thoughts to the console"""
        try:
            try:
                # Parse and print Assistant response
                assistant_reply_json = json_utils.fix_and_parse_json(assistant_reply)
            except json.JSONDecodeError as e:
                LOG.error(f"Error: Invalid JSON in assistant thoughts: {assistant_reply}, error: {repr(e)}")
                assistant_reply_json = json_utils.fix_json_by_finding_outermost_brackets(assistant_reply)

                assistant_reply_json = json_utils.fix_and_parse_json(assistant_reply_json)

            # Check if assistant_reply_json is a string and attempt to parse it into a
            #  JSON object
            if isinstance(assistant_reply_json, str):
                try:
                    assistant_reply_json = json.loads(assistant_reply_json)
                except json.JSONDecodeError as e:
                    LOG.error(f"Error: Invalid JSON: {assistant_reply}, error: {repr(e)}")
                    assistant_reply_json = (
                        json_utils.fix_json_by_finding_outermost_brackets(assistant_reply_json)
                    )

            assistant_thoughts = assistant_reply_json.get("thoughts", {})
            assistant_thoughts_text = assistant_thoughts.get("text")
            assistant_thoughts_reasoning = None
            assistant_thoughts_criticism = None
            assistant_thoughts_speak = None

            if assistant_thoughts:
                assistant_thoughts_reasoning = assistant_thoughts.get("reasoning")
                assistant_thoughts_criticism = assistant_thoughts.get("criticism")
                assistant_thoughts_speak = assistant_thoughts.get("speak")

            thoughts_text = ""
            if assistant_thoughts_reasoning:
                thoughts_text += f"推理：{assistant_thoughts_reasoning}\n"
            if assistant_thoughts_text:
                thoughts_text += f"思考：{assistant_thoughts_text}\n"
            if assistant_thoughts_criticism:
                thoughts_text += f"反思：{assistant_thoughts_criticism}\n"

            self.console.print(Panel(thoughts_text,
                                     title=f"{self.ai_prefix.upper()}的内心独白",
                                     highlight=True, style='dim'))
            # it's useful for avoid splitting Panel
            LOG.info(f"{self.ai_prefix.upper()}的内心独白: {thoughts_text}")
            
            return assistant_reply_json
        except json.decoder.JSONDecodeError as e:
            call_stack = traceback.format_exc()
            LOG.error(f"Error: Invalid JSON: {assistant_reply}\n")
            LOG.error(f"Traceback: {repr(call_stack)}, error: {repr(e)}")

        # All other errors, return "Error: + error message"
        except Exception as e:
            call_stack = traceback.format_exc()
            LOG.error(f"Traceback: {repr(call_stack)}, error: {repr(e)}")

    @classmethod
    def from_llm_and_tools(
            cls,
            llm: BaseLLM,
            tools: Sequence[BaseTool],
            console: Console = Console(),
            callback_manager: Optional[BaseCallbackManager] = None,
            prefix: str = PREFIX,
            suffix: str = SUFFIX,
            format_instructions: str = FORMAT_INSTRUCTIONS,
            ai_prefix: str = default_ai_prefix,
            human_prefix: str = default_human_prefix,
            input_variables: Optional[List[str]] = None,
            **kwargs: Any,
    ) -> Bot:
        """Construct an bot from an LLM and tools."""
        prompt = cls.create_prompt(
            tools,
            ai_prefix=ai_prefix,
            human_prefix=human_prefix,
            prefix=prefix,
            suffix=suffix,
            format_instructions=format_instructions,
            input_variables=input_variables,
        )
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            callback_manager=callback_manager,
        )
        tool_names = [tool.name for tool in tools]
        return cls(
            llm_chain=llm_chain, console=console, allowed_tools=tool_names, ai_prefix=ai_prefix, **kwargs
        )
