"""Functionality for loading apps."""
from chatgpt_tool_hub.apps.lite_app import LiteApp
from chatgpt_tool_hub.apps.victorinox import Victorinox

APP_TO_CLASS = {
    "lite": LiteApp,
    "victorinox": Victorinox
}
