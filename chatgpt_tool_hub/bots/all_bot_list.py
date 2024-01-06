"""Functionality for loading bots."""

from . import ChatBot, QABot


BOT_TO_CLASS = {
    "qa-bot": QABot,
    "chat-bot": ChatBot,
    "default": QABot,
}
