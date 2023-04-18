"""Generic utility functions."""
import os
import random
import string
from typing import Any, Dict, Optional


def get_from_dict_or_env(
        data: Dict[str, Any], key: str, env_key: str, default: Optional[Any] = None
) -> Any:
    """Get a value from a dictionary or an environment variable."""
    if key in data and data[key]:
        return data[key]
    elif env_key in os.environ and os.environ[env_key]:
        return os.environ[env_key]
    elif default is not None:
        return default
    else:
        raise ValueError(
            f"Did not find {key}, please add an environment variable"
            f" `{env_key}` which contains it, or pass"
            f"  `{key}` as a named parameter."
        )


def generate_random_filename(figure_num: int = 10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(figure_num))
