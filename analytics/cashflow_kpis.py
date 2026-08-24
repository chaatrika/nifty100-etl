def compute_cashflow_kpis(cfo, cfi, cff, pat_5yr_avg, sales, op_profit):
    """Computes FCF, CFO Quality, CapEx Intensity, FCF Conversion, and Allocation Pattern."""
    cfo, cfi, cff = cfo or 0, cfi or 0, cff or 0
    fcf = cfo + cfi

    # 1. CFO Quality Score
    cfo_score = (cfo / pat_5yr_avg) if pat_5yr_avg else None
    if not cfo_score:
        q_label = "Unknown"
    else:
        q_label = "High Quality" if cfo_score > 1.0 else ("Moderate" if cfo_score >= 0.5 else "Accrual Risk")

    # 2. CapEx Intensity
    capex = (abs(cfi) / sales * 100) if sales and sales > 0 else None
    if capex is None:
        c_label = "Unknown"
    else:
        c_label = "Asset Light" if capex < 3.0 else ("Moderate" if capex <= 8.0 else "Capital Intensive")

    # 3. Capital Allocation 8-Pattern Classifier
    signs = ("+" if cfo >= 0 else "-", "+" if cfi >= 0 else "-", "+" if cff >= 0 else "-")
    patterns = {
        ("+", "-", "-"): "Shareholder Returns" if (cfo_score and cfo_score > 1.0) else "Reinvestor",
        ("+", "+", "-"): "Liquidating Assets",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "-"): "Pre-Revenue"
    }

    return {
        "free_cash_flow": fcf,
        "cfo_quality_score": cfo_score,
        "cfo_quality_label": q_label,
        "capex_intensity": capex,
        "capex_label": c_label,
        "fcf_conversion": (fcf / op_profit * 100) if op_profit else None,
        "cfo_sign": signs[0],
        "cfi_sign": signs[1],
        "cff_sign": signs[2],
        "pattern_label": patterns.get(signs, "Mixed")
    }