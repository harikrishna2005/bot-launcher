import pytest
from pydantic import BaseModel, ValidationError
from shared.domain.models.common.symbol import Symbol


# A simple model to test Pydantic integration
class SymbolTestModel(BaseModel):
    symbol: Symbol


class TestSymbol:

    @pytest.mark.parametrize("input_str, expected", [
        ("btc_usdt", "BTC/USDT"),  # Underscore to Slash + Upper
        ("ETH-BTC", "ETH/BTC"),  # Dash to Slash
        ("sol/usdc", "SOL/USDC"),  # Lower to Upper
        ("  btc/usdt  ", "BTC/USDT"),  # Whitespace (if you add .strip() to __new__)
    ])
    def test_normalization(self, input_str, expected):
        """Verify that various messy inputs are converted to canonical BASE/QUOTE."""
        s = Symbol(input_str)
        assert s == expected
        assert "/" in s
        assert s.isupper()

    def test_base_and_quote_properties(self):
        """Verify the split logic for base and quote assets."""
        s = Symbol("BTC/USDT")
        assert s.base == "BTC"
        assert s.quote == "USDT"

    def test_with_separator(self):
        """Verify we can morph the symbol for different exchange APIs."""
        s = Symbol("BTC/USDT")
        assert s.with_separator("_") == "BTC_USDT"
        assert s.with_separator("-") == "BTC-USDT"
        assert s.with_separator("") == "BTCUSDT"

    def test_pydantic_integration_success(self):
        """Verify Pydantic automatically converts strings to Symbol objects."""
        data = {"symbol": "eth_usdt"}
        model = SymbolTestModel(**data)

        assert isinstance(model.symbol, Symbol)
        assert model.symbol == "ETH/USDT"
        assert model.symbol.base == "ETH"

    def test_is_string_compatible(self):
        """Ensure Symbol behaves like a standard string (concatenation, etc)."""
        s = Symbol("BTC/USDT")
        # Should be able to use in f-strings and string methods
        assert f"Pair: {s}" == "Pair: BTC/USDT"
        assert s.lower() == "btc/usdt"
        assert len(s) == 8

    def test_immutability(self):
        """Since it's a str subclass, it should not allow attribute assignment."""
        s = Symbol("BTC/USDT")
        with pytest.raises(AttributeError):
            s.base = "ETH"  # Properties are read-only