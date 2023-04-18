"""Functionality for loading bots."""

from chatgpt_tool_hub.bots import ChatBot
from chatgpt_tool_hub.bots import QABot


BOT_TO_CLASS = {
    "qa-bot": QABot,
    "chat-bot": ChatBot,
    "default": QABot,
}
