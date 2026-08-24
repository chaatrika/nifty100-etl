def calculate_cagr(start, end, years):
    """Calculates CAGR and handles edge cases."""
    # 1. Missing or invalid input checks
    if not years or years <= 0 or start is None or end is None:
        return None, "INSUFFICIENT"

    # 2. Zero starting base
    if start == 0:
        return None, "ZERO_BASE"

    # 3. Normal CAGR calculation
    if start > 0 and end > 0:
        cagr = ((end / start) ** (1 / years) - 1) * 100
        return round(cagr, 2), "NORMAL"

    # 4. Negative number edge cases
    if start > 0 and end < 0:
        return None, "DECLINE_TO_LOSS"
    if start < 0 and end > 0:
        return None, "TURNAROUND"
    if start < 0 and end < 0:
        return None, "BOTH_NEGATIVE"

    return None, "UNKNOWN"