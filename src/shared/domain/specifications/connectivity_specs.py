from abc import ABC, abstractmethod
from typing import Any

class IConnectivitySpecification(ABC):
    """
    Blueprint for rules checking if a resource (API, Container, DB)
    is reachable and responding.
    """
    @abstractmethod
    async def is_satisfied(self, connector: Any) -> bool:
        pass

    @abstractmethod
    def get_error(self) -> str:
        pass