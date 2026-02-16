from pydantic import BaseModel, Field
from typing import Dict
from shared.domain.models.common.symbol import Symbol


class RebalanceStrategy(BaseModel):
    """
    Defines the desired state of the portfolio.
    Example: {"BTC/USDT": 0.5, "PAXG/USDT": 0.5}
    (50% Bitcoin, 50% Cash)
    """
    targets: Dict[Symbol, float]  # Symbol name -> Percentage (0.0 to 1.0)
    threshold: float = 0.01  # 1% drift required before trading
    interval_sec: int = 60  # How often to check

    @property
    def total_weight(self):
        return sum(self.targets.values())