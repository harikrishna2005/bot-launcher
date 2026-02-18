"""
Domain models for Exchange Market Data.

This module defines the static constraints and rules fetched from external
exchanges (e.g., Binance, Kraken). These models represent the 'laws' of the
market that the bot must obey, such as order sizing and precision limits.

# This model class contains data classes related to  data coming from the exchange (rules, limits, order books).

"""

"""
Trading Term        Grocery Store Equivalent        Example (BTC/USDT)
-----------------------------------------------------------------------
Quantity (Amount)	Number of Apples	            0.5 BTC
Price	            Price per Apple	                $50,000
Cost (Notional)	    Total bill at the register	    $25,000
"""


from pydantic import BaseModel, model_validator
from typing import Optional
from decimal import Decimal
from typing import Tuple

from shared.domain.models.common.symbol import Symbol
from shared.utils.precision_utils import (
    decimal_to_precision,
    TRUNCATE,
    ROUND,
    DECIMAL_PLACES,
    TICK_SIZE
)



class MarketRules(BaseModel):
    """
        Validation model for exchange-related trading limits.
        Static constraints for a specific symbol provided by the exchange.

        Attributes:
            symbol: The trading pair (e.g., 'BTC/USDT').
            min_cost: Minimum total cost of the order in quote currency ($).
            min_qty_amt: Smallest quantity of the base asset (e.g., 0.001 BTC).
            price_precision: Max decimal places allowed for the Price.
            amount_precision: Max decimal places allowed for the Quantity/Amount.
        Explanation:
        
        1. min_notional (The "Value" Limit)
                What it is: The minimum Total Dollar Value ($) of the trade.
                
                The Logic: Price × Amount = Notional.
                
                Example: On Binance, this is often $5.00.
                
                        If you try to buy $2.00 worth of BTC, the exchange says: "Too small! Not worth our time." * You must spend at least $5.00.
        
        2. min_amount (The "Quantity" Limit)
                What it is: The minimum Physical Amount of the coin you can buy/sell.
                
                Example: For Bitcoin, this might be 0.0001 BTC.
                
                        Even if you have $100, if you try to buy 0.00000001 BTC, the exchange will reject it because the quantity is too microscopic for their system to track.
        
        3. price_precision (The "Price Decimals")
                What it is: How many digits are allowed after the decimal point in the Price.
                
                Example: If precision is 2:
                
                        Allowed: $50,000.12
                        
                        Rejected: $50,000.1234 (Too many decimals).

        4. amount_precision (The "Quantity Decimals")
                What it is: How many digits are allowed after the decimal point in the Quantity.
                
                Example: If precision is 4:
                
                        Allowed: 0.1234 BTC
                        
                        Rejected: 0.123456 BTC (The exchange "rounds off" after 4 digits).




    QUESTION:  Is price_precision the same as tick_size?
                Not exactly, but they are related.

                Precision (Digits): This refers to the number of decimal places. For example, a precision of 2 means 50000.12.

                Tick Size (Increment): This refers to the smallest allowed movement. For example, a tick size of 0.05 means you can have 50000.10 or 50000.15, but not 50000.12.
        """
    symbol: Symbol
    min_cost: float     #  min_notional or min_cost Total value of trade - Minimum cost in quote currency (e.g., $10)
    min_qty_amt: float       #  Quantity of asset   - Minimum amount of base asset (e.g., 0.001 BTC)
    price_precision: float    #  Decimal places for price Example: 2 means you can have $50,000.12 but not $50,000.123       Tick Size (price)
    qty_amt_precision: float   #  Decimal places for quantity Example: 4 means you can have 0.1234 BTC but not 0.123456 BTC   Step Size (amount)
    # Pre-calculated modes for high-speed access
    price_mode: Optional[int] = None
    qty_amt_mode: Optional[int] = None


    @model_validator(mode='after')
    def determine_precision_modes(self) -> 'MarketRules':
        # 1. Price Mode Detection
        # If it's an integer (0, 1, 2...) -> DECIMAL_PLACES
        # If it's a small float (0.001) -> TICK_SIZE
        if self.price_precision >= 1.0 or self.price_precision == 0:
            self.price_mode = DECIMAL_PLACES
            self.price_precision = int(self.price_precision)
        else:
            self.price_mode = TICK_SIZE

        # 2. Amount Mode Detection
        if self.qty_amt_precision >= 1.0 or self.qty_amt_precision == 0:
            self.qty_amt_mode = DECIMAL_PLACES
            self.qty_amt_precision = int(self.qty_amt_precision)
        else:
            self.qty_amt_mode = TICK_SIZE

        return self

    def qty_amt_to_precision(self, amount: float) -> str:
        """
        Returns the STRING representation (Exact CCXT style).
        Use this for the final API call.
        """
        if amount is None: return "0"
        return decimal_to_precision(
            amount,
            rounding_mode=TRUNCATE,
            precision=self.qty_amt_precision,
            counting_mode=self.qty_amt_mode
        )

    def price_to_precision(self, price: float) -> str:
        """
        Returns the STRING representation (Exact CCXT style).
        Use this for the final API call.
        """
        if price is None: return "0"
        return decimal_to_precision(
            price,
            rounding_mode=ROUND,
            precision=self.price_precision,
            counting_mode=self.price_mode
        )

    # --- Performance Helpers for Rebalancer Core ---

    def clean_qty_amt(self, amount: float) -> float:
        """Helper to get a float version for internal logic/comparisons."""
        return float(self.qty_amt_to_precision(amount))

    def clean_price(self, price: float) -> float:
        """Helper to get a float version for internal logic/comparisons."""
        return float(self.price_to_precision(price))

    def is_valid_trade(self, qty_amt: float, price: float) -> Tuple[bool, str]:
        """
        Validates if the proposed trade satisfies exchange minimums.

        Args:
            qty_amt: The raw quantity/amount of the base asset.
            price: The raw price of the asset.

        Returns:
            (is_valid, error_message): Tuple where bool is True if valid.
        """
        # 1. Normalize values to exchange precision (The 'Clean' versions)
        # This mirrors exactly what the exchange will process.
        final_qty = self.clean_qty_amt(qty_amt)
        final_price = self.clean_price(price)

        # 2. Calculate Total Cost (Notional) using Decimal for 100% accuracy.
        # Initialize Decimal from strings to avoid float artifacts.
        d_qty = Decimal(str(final_qty))
        d_price = Decimal(str(final_price))
        total_cost = float(d_qty * d_price)

        # 3. Rule Check: Minimum Quantity (Base Asset)
        if final_qty < self.min_qty_amt:
            return False, (
                f"Trade rejected: {self.symbol} quantity {final_qty} "
                f"is below minimum {self.min_qty_amt}."
            )

        # 4. Rule Check: Minimum Cost (Quote Currency/Notional)
        if total_cost < self.min_cost:
            return False, (
                f"Trade rejected: {self.symbol} total cost ${total_cost:.4f} "
                f"is below minimum ${self.min_cost:.2f}."
            )

        return True, ""