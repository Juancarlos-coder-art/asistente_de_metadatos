from abc import ABC, abstractmethod
from typing import Generator


class BaseReader(ABC):
    def __init__(self, path: str):
        self.path = path

    @abstractmethod
    def stream_records(self) -> Generator[dict, None, None]:
        """Yield one record (flat dict) at a time from the file."""
        ...
