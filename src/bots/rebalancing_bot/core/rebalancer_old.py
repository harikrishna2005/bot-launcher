from typing import Dict, List, Any


class Rebalancer:
    def __init__(self, target_weights: Dict[str, float], min_trade_usd: float = 10.0, threshold: float = 0.01):
        """
        :param target_weights: e.g. {"BTC": 0.5, "PAXG": 0.5}
        :param min_trade_usd: Minimum $ value the exchange allows (e.g. $10)
        :param threshold: Only trade if drift is > 1%
        """
        self.target_weights = target_weights
        self.min_trade_usd = min_trade_usd
        self.threshold = threshold

    def calculate_rebalance(self, holdings: Dict[str, float], prices: Dict[str, float]) -> List[Dict[str, Any]]:
        # 1. Calculate Current Market Value of each asset
        values = {asset: holdings[asset] * prices[asset] for asset in self.target_weights}
        total_value = sum(values.values())

        if total_value == 0:
            return []

        trades = []
        for asset, target_pct in self.target_weights.items():
            current_val = values[asset]
            current_pct = current_val / total_value

            # 2. Calculate Deviation (Drift)
            drift = current_pct - target_pct

            # 3. Only act if drift exceeds our threshold (e.g., 0.01 for 1%)
            if abs(drift) > self.threshold:
                target_value = total_value * target_pct
                diff_usd = target_value - current_val  # Positive = Buy, Negative = Sell

                # 4. Check against Exchange Minimum ($10 logic)
                if abs(diff_usd) >= self.min_trade_usd:
                    amount_to_trade = abs(diff_usd) / prices[asset]
                    trades.append({
                        "asset": asset,
                        "side": "buy" if diff_usd > 0 else "sell",
                        "amount": round(amount_to_trade, 8),
                        "value_usd": round(abs(diff_usd), 2),
                        "drift_pct": round(drift * 100, 2)
                    })

        return trades

    # Inside your Rebalancer class
    def filter_binance_rules(self, amount, price, symbol_rules):
        """
        symbol_rules would be data you get once from Binance API:
        e.g., {'minNotional': 10.0, 'stepSize': '0.0001'}
        """
        total_value = amount * price

        # 1. Check Min Notional ($10 rule)
        if total_value < float(symbol_rules['minNotional']):
            return 0

            # 2. Fix Precision (Step Size rule)
        # If stepSize is 0.0001, we need to round to 4 decimal places
        precision = str(symbol_rules['stepSize']).find('1') - 1
        if precision < 0: precision = 0

        return round(amount, precision)