"""An bot designed to hold a conversation in addition to using tools."""
from __future__ import annotations

import re
from typing import Any, List, Optional, Sequence, Tuple

from chatgpt_tool_hub.bots.bot import Bot
from chatgpt_tool_hub.bots.chat_bot.prompt import FORMAT_INSTRUCTIONS, PREFIX, SUFFIX
from chatgpt_tool_hub.chains import LLMChain
from chatgpt_tool_hub.common.callbacks import BaseCallbackManager
from chatgpt_tool_hub.models.base import BaseLLM
from chatgpt_tool_hub.prompts import PromptTemplate
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.common.log import LOG


class ChatBot(Bot):
    """An bot designed to hold a conversation in addition to using tools."""

    ai_prefix: str = "AI"

    @property
    def _bot_type(self) -> str:
        """Return Identifier of bot type."""
        return "chat-bot"

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "Observation: "

    def _fix_text(self, text: str) -> str:
        if not self.allowed_tools:
            tool_names = ""
        else:
            tool_names = ", ".join([tool for tool in self.allowed_tools])
        instruction_text = FORMAT_INSTRUCTIONS.format(
            tool_names=tool_names, ai_prefix=self.ai_prefix
        )
        _text = ("\n\n"
                 f"You just told me: {text}, but it doesn't meet the format I mentioned to you. \n\n"
                 f"format: {instruction_text}. \n\n"
                 "You should understand why you did not input the correct format, correct it and try again. \n\n")
        LOG.debug("(fix_text): fix_text: " + repr(_text))
        return _text

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
            ai_prefix: str = "AI",
            human_prefix: str = "Human",
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

        instruction_text = format_instructions.format(
            tool_names=tool_names, ai_prefix=ai_prefix
        )
        template = "\n\n".join([prefix, tool_strings, instruction_text, suffix])
        if input_variables is None:
            input_variables = ["input", "chat_history", "bot_scratchpad"]
        prompt = PromptTemplate(template=template, input_variables=input_variables)

        LOG.debug("\nprompt: " + str(prompt) + "\n")
        return prompt

    @property
    def finish_tool_name(self) -> str:
        """Name of the tool to use to finish the chain."""
        return self.ai_prefix

    def _extract_tool_and_input(self, llm_output: str) -> Optional[Tuple[str, str]]:
        # todo this is bad parsing rule
        if f"{self.ai_prefix}:" in llm_output:
            return self.ai_prefix, llm_output.split(f"{self.ai_prefix}:")[-1].strip()
        regex = r"Action: (.*?)[\n]*Action Input: (.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            return None

        action = match.group(1)
        action_input = match.group(2)
        LOG.info(f"执行Tool: {action}中...")
        return action.strip(), action_input.strip(" ").strip('"')

    @classmethod
    def from_llm_and_tools(
            cls,
            llm: BaseLLM,
            tools: Sequence[BaseTool],
            callback_manager: Optional[BaseCallbackManager] = None,
            prefix: str = PREFIX,
            suffix: str = SUFFIX,
            format_instructions: str = FORMAT_INSTRUCTIONS,
            ai_prefix: str = "AI",
            human_prefix: str = "Human",
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
            llm_chain=llm_chain, allowed_tools=tool_names, ai_prefix=ai_prefix, **kwargs
        )
