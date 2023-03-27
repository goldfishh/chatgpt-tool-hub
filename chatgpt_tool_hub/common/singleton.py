import threading
from typing import Any


class Singleton:
    """A thread-safe singleton class that can be inherited from."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> Any:
        """Create a new shared instance of the class."""
        if cls._instance is None:
            with cls._lock:
                # Another thread could have created the instance
                # before we acquired the lock. So check that the
                # instance is still nonexistent.
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
