import pytest

from shared.domain.models.market import MarketRules
from shared.domain.models.common.symbol import Symbol
from shared.utils.precision_utils import DECIMAL_PLACES, TICK_SIZE


@pytest.mark.parametrize(
    "price_precision, amount_precision, expected_price_mode, expected_amount_mode, expected_price_type, expected_amount_type",
    [
        # Both provided as whole-number precisions -> coerced to int & DECIMAL_PLACES
        (2, 4, DECIMAL_PLACES, DECIMAL_PLACES, int, int),
        # Both small step sizes -> keep float & TICK_SIZE
        (0.01, 0.001, TICK_SIZE, TICK_SIZE, float, float),
        # Mixed: zero treated as DECIMAL_PLACES, small float as TICK_SIZE
        (0, 0.0001, DECIMAL_PLACES, TICK_SIZE, int, float),
    ],
)
def test_precision_modes_are_inferred(
    price_precision,
    amount_precision,
    expected_price_mode,
    expected_amount_mode,
    expected_price_type,
    expected_amount_type,
):
    rules = MarketRules(
        symbol=Symbol("btc_usdt"),
        min_cost=10.0,
        min_qty_amt=0.001,
        price_precision=price_precision,
        qty_amt_precision=amount_precision,
    )

    assert rules.price_mode == expected_price_mode
    assert rules.qty_amt_mode == expected_amount_mode
    assert isinstance(rules.price_precision, expected_price_type)
    assert isinstance(rules.qty_amt_precision, expected_amount_type)

    # When DECIMAL_PLACES is chosen the precision is coerced to int for speed
    if expected_price_mode == DECIMAL_PLACES:
        assert rules.price_precision == int(price_precision)
    if expected_amount_mode == DECIMAL_PLACES:
        assert rules.qty_amt_precision == int(amount_precision)


@pytest.mark.parametrize(
    "price, price_precision, expected_str, expected_float",
    [
        (123.456, 2, "123.46", 123.46),             # DECIMAL_PLACES with rounding
        (123.5, 0, "124", 124.0),                   # Whole-number precision with rounding to integer
        (100.038, 0.05, "100.05", 100.05),          # TICK_SIZE rounding to nearest step
    ],
)
def test_price_to_precision(price, price_precision, expected_str, expected_float):
    rules = MarketRules(
        symbol=Symbol("btc_usdt"),
        min_cost=10.0,
        min_qty_amt=0.001,
        price_precision=price_precision,
        qty_amt_precision=4,  # default amount precision; not under test here
    )

    result_str = rules.price_to_precision(price)
    result_float = rules.clean_price(price)

    assert result_str == expected_str
    assert result_float == pytest.approx(expected_float)


@pytest.mark.parametrize(
    "amount, amount_precision, expected_str, expected_float",
    [
        (0.123456, 4, "0.1234", 0.1234),            # DECIMAL_PLACES with truncation
        (5.9, 0, "5", 5.0),                         # Integer precision with truncation
        (0.12349, 0.001, "0.123", 0.123),           # TICK_SIZE with truncation to nearest lower step
    ],
)
def test_amount_to_precision(amount, amount_precision, expected_str, expected_float):
    rules = MarketRules(
        symbol=Symbol("btc_usdt"),
        min_cost=10.0,
        min_qty_amt=0.001,
        price_precision=2,  # default price precision; not under test here
        qty_amt_precision=amount_precision,
    )

    result_str = rules.qty_amt_to_precision(amount)
    result_float = rules.clean_qty_amt(amount)

    assert result_str == expected_str
    assert result_float == pytest.approx(expected_float)


@pytest.mark.parametrize(
    "qty, price, price_precision, qty_precision, min_qty, min_cost, expected_valid, error_substring",
    [
        # Truncation drops quantity below min_qty_amt
        (0.00099, 50000.0, 2, 3, 0.001, 10.0, False, "quantity"),
        # Rounding price down makes total cost miss the floor
        (1.0, 9.994, 2, 4, 0.0001, 10.0, False, "total cost"),
        # Rounding price up rescues the trade to meet min_cost
        (1.0, 9.995, 2, 4, 0.0001, 10.0, True, ""),
        # Smaller qty: rounding down keeps notional just under the threshold
        (0.1, 99.994, 2, 4, 0.0001, 10.0, False, "total cost"),
        # Smaller qty: rounding up nudges notional over the threshold
        (0.1, 99.995, 2, 4, 0.0001, 10.0, True, ""),
        (0.1, 99.995, 0.01, 0.00001, 0.00001, 5.0, True, ""),   # BIN
        (0.00008, 66371.73, 0.01, 0.00001, 0.00001, 5.0, True, ""),   # # BIN
        (0.00007, 66371.73, 0.01, 0.00001, 0.00001, 5.0, False, "total cost"),   # BIN
    ],
)
def test_validate_trade_respects_minimums_with_rounding(
    qty,
    price,
    price_precision,
    qty_precision,
    min_qty,
    min_cost,
    expected_valid,
    error_substring,
):
    rules = MarketRules(
        symbol=Symbol("btc_usdt"),
        min_cost=min_cost,
        min_qty_amt=min_qty,
        price_precision=price_precision,
        qty_amt_precision=qty_precision,
    )

    is_valid, error = rules.is_valid_trade(qty, price)

    assert is_valid is expected_valid
    if expected_valid:
        assert error == ""
    else:
        assert error_substring.lower() in error.lower()
        cleaned_qty = rules.clean_qty_amt(qty)
        cleaned_price = rules.clean_price(price)
        total_cost = cleaned_qty * cleaned_price
        if "quantity" in error_substring.lower():
            assert cleaned_qty < min_qty
        if "total cost" in error_substring.lower():
            assert total_cost < min_cost

