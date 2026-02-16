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
        min_notional=10.0,
        min_amount=0.001,
        price_precision=price_precision,
        amount_precision=amount_precision,
    )

    assert rules.price_mode == expected_price_mode
    assert rules.amount_mode == expected_amount_mode
    assert isinstance(rules.price_precision, expected_price_type)
    assert isinstance(rules.amount_precision, expected_amount_type)

    # When DECIMAL_PLACES is chosen the precision is coerced to int for speed
    if expected_price_mode == DECIMAL_PLACES:
        assert rules.price_precision == int(price_precision)
    if expected_amount_mode == DECIMAL_PLACES:
        assert rules.amount_precision == int(amount_precision)


@pytest.mark.parametrize(
    "price, price_precision, expected_str, expected_float",
    [
        # DECIMAL_PLACES with rounding
        (123.456, 2, "123.46", 123.46),
        # Whole-number precision with rounding to integer
        (123.5, 0, "124", 124.0),
        # TICK_SIZE rounding to nearest step
        (100.038, 0.05, "100.05", 100.05),
    ],
)
def test_price_to_precision(price, price_precision, expected_str, expected_float):
    rules = MarketRules(
        symbol=Symbol("btc_usdt"),
        min_notional=10.0,
        min_amount=0.001,
        price_precision=price_precision,
        amount_precision=4,  # default amount precision; not under test here
    )

    result_str = rules.price_to_precision(price)
    result_float = rules.clean_price(price)

    assert result_str == expected_str
    assert result_float == pytest.approx(expected_float)


@pytest.mark.parametrize(
    "amount, amount_precision, expected_str, expected_float",
    [
        # DECIMAL_PLACES with truncation
        (0.123456, 4, "0.1234", 0.1234),
        # Integer precision with truncation
        (5.9, 0, "5", 5.0),
        # TICK_SIZE with truncation to nearest lower step
        (0.12349, 0.001, "0.123", 0.123),
    ],
)
def test_amount_to_precision(amount, amount_precision, expected_str, expected_float):
    rules = MarketRules(
        symbol=Symbol("btc_usdt"),
        min_notional=10.0,
        min_amount=0.001,
        price_precision=2,  # default price precision; not under test here
        amount_precision=amount_precision,
    )

    result_str = rules.amount_to_precision(amount)
    result_float = rules.clean_amount(amount)

    assert result_str == expected_str
    assert result_float == pytest.approx(expected_float)
