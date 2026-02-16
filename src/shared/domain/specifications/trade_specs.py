from abc import ABC, abstractmethod
from typing import Any

class ITradeSpecification(ABC):
    @abstractmethod
    def is_satisfied_by(self, trade: Any, context: Any) -> bool:
        pass

    @abstractmethod
    def get_error(self) -> str:
        pass