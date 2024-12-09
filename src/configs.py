from dataclasses import dataclass
from typing import Callable

from src.utils import UploadStrategy, S3UploadStrategy, LocalUploadStrategy


@dataclass
class UploadStrategies:
    online: Callable[[], UploadStrategy]
    local: Callable[[], UploadStrategy]

    def get_strategy(self, upload_type: str) -> UploadStrategy:
        """
        Dynamically fetch the correct strategy based on client input
        """

        strategy_creator = getattr(self, upload_type, None)
        if not strategy_creator:
            raise ValueError(f"Unsupported upload type: {upload_type} ")
        strategy_instance = strategy_creator()
        if not isinstance(strategy_instance, UploadStrategy):
            raise TypeError(f"Strategy is not of type UploadStrategy: {strategy_instance}")

        return strategy_instance