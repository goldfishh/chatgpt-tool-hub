from __future__ import annotations

import re
from typing import Any, List, Optional, Sequence, Tuple

from rich.console import Console

from chatgpt_tool_hub.bots.qa_bot.prompt import FORMAT_INSTRUCTIONS, PREFIX, SUFFIX
from chatgpt_tool_hub.chains import LLMChain
from chatgpt_tool_hub.common.callbacks import BaseCallbackManager
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.engine import Bot
from chatgpt_tool_hub.models.base import BaseLLM
from chatgpt_tool_hub.prompts import PromptTemplate
from chatgpt_tool_hub.tools.base_tool import BaseTool

FINAL_ANSWER_ACTION = "Final Answer:"


class QABot(Bot):
    """Bot for the MRKL chain."""

    @property
    def _bot_type(self) -> str:
        """Return Identifier of bot type."""
        return "qa-bot"

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "Observation: "

    @property
    def llm_prefix(self) -> str:
        """Prefix to append the llm call with."""
        return "Thought:"

    def _fix_text(self, text: str) -> str:
        tool_names = ", ".join(list(self.allowed_tools)) if self.allowed_tools else ""
        instruction_text = FORMAT_INSTRUCTIONS.format(tool_names=tool_names)
        return f"\n\nYou just told me: {text}, but it doesn't meet the format I mentioned to you. \n\nformat: {instruction_text}. \n\nYou should understand why you did not input the correct format, correct it and try again. \n\n"

    @classmethod
    def create_prompt(
        cls,
        tools: Sequence[BaseTool],
        prefix: str = PREFIX,
        suffix: str = SUFFIX,
        format_instructions: str = FORMAT_INSTRUCTIONS,
        input_variables: Optional[List[str]] = None,
    ) -> PromptTemplate:
        """Create prompt in the style of the zero shot bot.

        Args:
            tools: List of tools the bot will have access to, used to format the
                prompt.
            prefix: String to put before the list of tools.
            suffix: String to put after the list of tools.
            input_variables: List of input variables the final prompt will expect.

        Returns:
            A PromptTemplate with the template assembled from the pieces here.
        """
        tool_strings = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
        tool_names = ", ".join([tool.name for tool in tools])
        format_instructions = format_instructions.format(tool_names=tool_names)
        template = "\n\n".join([prefix, tool_strings, format_instructions, suffix])
        if input_variables is None:
            input_variables = ["input", "bot_scratchpad"]
        return PromptTemplate(template=template, input_variables=input_variables)

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
        input_variables: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Bot:
        """Construct an bot from an LLM and tools."""
        cls._validate_tools(tools)
        prompt = cls.create_prompt(
            tools,
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
        return cls(llm_chain=llm_chain, console=console, allowed_tools=tool_names, **kwargs)

    @classmethod
    def _validate_tools(cls, tools: Sequence[BaseTool]) -> None:
        for tool in tools:
            if tool.description is None:
                raise ValueError(
                    f"Got a tool {tool.name} without a description. For this bot, "
                    f"a description must always be provided."
                )

    def _extract_tool_and_input(self, text: str) -> Optional[Tuple[str, str]]:
        """Parse out the action and input from the LLM output.

        Note: if you're specifying a custom prompt for the QABot,
        you will need to ensure that it meets the following Regex requirements.
        The string starting with "Action:" and the following string starting
        with "Action Input:" should be separated by a newline.
        """
        if FINAL_ANSWER_ACTION in text:
            return "Final Answer", text.split(FINAL_ANSWER_ACTION)[-1].strip()
        regex = r"Action: (.*?)[\n]*Action Input: (.*)"
        match = re.search(regex, text, re.DOTALL)
        if not match:
            return None

        action = match[1].strip()
        action_input = match[2]
        LOG.info(f"执行Tool: {action}中...")

        return action, action_input.strip(" ")
