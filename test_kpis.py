from main_pipeline import calculate_all_metrics

def test_profitability_and_debt_free():
    npm, roe, de, icr, icr_label, cagr, cagr_flag, fcf, pattern = calculate_all_metrics(
        sales=1000, net_profit=150, equity=500, reserves=300,
        borrowings=0, interest=0, cfo=200, cfi=-50, cff=-30, start_sales_5yr=600, sector="IT"
    )
    assert npm == 15.0
    assert roe == 18.75
    assert de == 0.0
    assert icr_label == "Debt Free"

def test_cagr_turnaround_edge_case():
    npm, roe, de, icr, icr_label, cagr, cagr_flag, fcf, pattern = calculate_all_metrics(
        sales=1000, net_profit=150, equity=500, reserves=300,
        borrowings=10, interest=5, cfo=100, cfi=-20, cff=-10, start_sales_5yr=-500, sector="IT"
    )
    assert cagr is None
    assert cagr_flag == "TURNAROUND"

def test_cagr_insufficient_data():
    npm, roe, de, icr, icr_label, cagr, cagr_flag, fcf, pattern = calculate_all_metrics(
        sales=1000, net_profit=150, equity=500, reserves=300,
        borrowings=10, interest=5, cfo=100, cfi=-20, cff=-10, start_sales_5yr=None, sector="IT"
    )
    assert cagr is None
    assert cagr_flag == "INSUFFICIENT"

