from abc import ABC, abstractmethod
from typing import Any, Generator


class BaseExtractor(ABC):
    """
    Contract for all metadata extractors.

    An extractor processes a stream of records (dicts) and returns a
    structured result dict. Subclasses must implement:
      - name        : short identifier used as the result key
      - update()    : called once per record during streaming
      - result()    : called once after all records have been consumed
    """

    name: str = "base"

    def __init__(self, file_path: str = "", input_json: dict | None = None) -> None:
        self.file_path = file_path
        self.input_json = input_json or {}

    @staticmethod
    def has_content(val: Any) -> bool:
        if val is None:
            return False
        if isinstance(val, str):
            return bool(val.strip())
        if isinstance(val, (list, dict)):
            return len(val) > 0
        return True

    @abstractmethod
    def update(self, record: dict) -> None:
        """Consume one record from the stream."""
        ...

    @abstractmethod
    def result(self) -> dict[str, Any]:
        """Return the extracted metadata after all records are processed."""
        ...

    def finalize(self, results: dict, df: "pd.DataFrame | None") -> dict[str, Any]:
        """Optional post-streaming step called after all extractors have run result().

        Receives the merged results dict and the loaded DataFrame (may be None).
        Return a dict to be merged into the output, or {} to contribute nothing.
        """
        return {}
