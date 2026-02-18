"""
Business Rule: Minimum Order Validation.

This module implements the logic to ensure a trade meets the exchange's
minimum requirements (Notional value) before it is sent to the order book.
"""

from shared.domain.specifications.trade_specs import ITradeSpecification
from shared.domain.models.market import MarketRules
from shared.domain.models.trading import TradeCandidate


class MinimumOrderRule(ITradeSpecification):
    """
    Validates if a trade is large enough for the exchange to process.

    This rule checks the 'Notional Value' (Price * Amount) against
    the minimum limits set by the exchange for a specific symbol.
    """

    def __init__(self):
        self._error = ""

    def is_satisfied_by(self, trade: TradeCandidate, rules: MarketRules) -> bool:
        """
        Checks if the trade value meets the min_notional requirement.

        Args:
            trade: The proposed trade (contains symbol, amount, price).
            rules: The pre-fetched market constraints (contains min_notional).

        Returns:
            bool: True if valid, False if the trade is too small.
        """
        # Calculate the total cost of the trade in quote currency (e.g., USDT)
        # Formula: Total Value = Quantity * Price
        trade_value = trade.amount * trade.price

        if trade_value < rules.min_cost:
            self._error = (
                f"Trade for {trade.symbol} rejected: Value ${trade_value:.2f} "
                f"is below the minimum required ${rules.min_cost:.2f}."
            )
            return False

        return True

    def get_error(self) -> str:
        """Returns the error message if the rule was not satisfied."""
        return self._error