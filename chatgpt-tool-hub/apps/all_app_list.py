"""Functionality for loading apps."""
from apps.lite_app import LiteApp
from apps.victorinox import Victorinox

APP_TO_CLASS = {
    "lite": LiteApp,
    "victorinox": Victorinox
}
