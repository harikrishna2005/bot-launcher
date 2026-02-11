from abc import ABC, abstractmethod
from typing import Dict, Any


class ExecutionStrategy(ABC):
    """Base class for bot execution strategies (local subprocess or Docker)"""

    @abstractmethod
    def launch_bot(self, bot_name: str, bot_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Launch a bot with the given configuration."""
        pass

    @abstractmethod
    def stop_bot(self, bot_name: str) -> Dict[str, str]:
        """Stop a running bot."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get the status of all running bots."""
        pass

    @abstractmethod
    def list_bots(self) -> Dict[str, Any]:
        """List all active bots."""
        pass

