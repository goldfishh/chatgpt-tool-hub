"""Functionality for loading bots."""

from chatgpt_tool_hub.bots.chat_bot.base import ChatBot
from chatgpt_tool_hub.bots.qa_bot.base import QABot


BOT_TO_CLASS = {
    "qa-bot": QABot,
    "chat-bot": ChatBot,
    "default": QABot,
}
