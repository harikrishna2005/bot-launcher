import math

def round_step(value: float, precision: int) -> float:
    """
    Standard helper to round a value to a specific decimal precision.
    Example: round_step(0.123456, 4) -> 0.1234
    """
    if precision <= 0:
        return float(math.floor(value))
    factor = 10 ** precision
    return math.floor(value * factor) / factor