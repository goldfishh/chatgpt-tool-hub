"""Load bot."""
from typing import Any, Optional, Sequence

from rich.console import Console

from chatgpt_tool_hub.bots.all_bot_list import BOT_TO_CLASS
from chatgpt_tool_hub.common.callbacks import BaseCallbackManager
from chatgpt_tool_hub.common.callbacks import get_callback_manager
from chatgpt_tool_hub.engine import ToolEngine
from chatgpt_tool_hub.models.base import BaseLanguageModel
from chatgpt_tool_hub.tools.base_tool import BaseTool


def init_tool_engine(
    tools: Sequence[BaseTool],
    llm: BaseLanguageModel,
    bot: Optional[str] = None,
    console: Console = Console(),
    callback_manager: Optional[BaseCallbackManager] = get_callback_manager(),
    bot_kwargs: Optional[dict] = None,
    **kwargs: Any,
) -> ToolEngine:
    """Load an bot executor given tools and LLM.

    Args:
        tools: List of tools this bot has access to.
        llm: Language model to use as the bot.
        bot: A string that specified the bot type to use. Valid options are:
            `qa-bot`
            `chat-bot`
            `catgirl-bot`
           If None, will default to
            `qa-bot`.
        console: rich.Console print rich text
        callback_manager: CallbackManager to use. Global callback manager is used if
            not provided. Defaults to None.
        bot_kwargs: Additional key word arguments to pass to the underlying bot
        **kwargs: Additional key word arguments passed to the bot executor

    Returns:
        An bot executor
    """

    if bot not in BOT_TO_CLASS:
        raise ValueError(
            f"Got unknown bot type: {bot}. "
            f"Valid types are: {BOT_TO_CLASS.keys()}."
        )
    if bot is None:
        bot = "default"
    bot_cls = BOT_TO_CLASS[bot]

    bot_kwargs = bot_kwargs or {}
    bot_obj = bot_cls.from_llm_and_tools(
        llm, tools, console, callback_manager=callback_manager, **bot_kwargs
    )

    return ToolEngine.from_bot_and_tools(
        bot=bot_obj,
        tools=tools,
        console=console,
        callback_manager=callback_manager,
        **kwargs,
    )
