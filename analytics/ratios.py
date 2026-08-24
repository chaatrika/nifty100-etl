def get_profitability(sales, net_profit, equity_capital, reserves, borrowings, total_assets):
    """Calculates NPM, ROE, ROCE, and ROA."""
    total_equity = equity_capital + reserves
    capital_employed = total_equity + borrowings

    return {
        # Net Profit Margin (%)
        "npm": (net_profit / sales * 100) if sales > 0 else None,
        
        # Return on Equity (%) - None if equity is 0 or negative
        "roe": (net_profit / total_equity * 100) if total_equity > 0 else None,
        
        # Return on Capital Employed (%)
        "roce": (net_profit / capital_employed * 100) if capital_employed > 0 else None,
        
        # Return on Assets (%)
        "roa": (net_profit / total_assets * 100) if total_assets > 0 else None
    }


def get_leverage_and_efficiency(borrowings, equity_capital, reserves, operating_profit, interest, investments, sales, total_assets, sector):
    """Calculates Debt-to-Equity, Interest Coverage, Net Debt, and Asset Turnover."""
    total_equity = equity_capital + reserves

    # Debt to Equity
    if borrowings == 0:
        de_ratio = 0.0
    else:
        de_ratio = (borrowings / total_equity) if total_equity > 0 else None

    # High Leverage Flag (Ignore for Banks/Financials)
    high_leverage = True if (de_ratio and de_ratio > 5.0 and sector != "Financials") else False

    # Interest Coverage Ratio (ICR)
    if interest == 0:
        icr, icr_label = None, "Debt Free"
    else:
        icr = operating_profit / interest
        icr_label = "Low Coverage" if icr < 1.5 else "Normal"

    return {
        "de_ratio": de_ratio,
        "high_leverage": high_leverage,
        "icr": icr,
        "icr_label": icr_label,
        "net_debt": borrowings - investments,
        "asset_turnover": (sales / total_assets) if total_assets > 0 else None
    }