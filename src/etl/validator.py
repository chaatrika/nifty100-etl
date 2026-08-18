import pandas as pd

def validate_null_values(df: pd.DataFrame, critical_cols: list[str], table_name: str) -> list[dict]:
    """DQ-02: Check for mandatory null values."""
    failures = []
    for col in critical_cols:
        if col in df.columns:
            null_rows = df[df[col].isna()]
            for _, row in null_rows.iterrows():
                failures.append({
                    "rule_id": "DQ-02",
                    "severity": "CRITICAL",
                    "table": table_name,
                    "record_id": row.get("company_id", "UNKNOWN"),
                    "details": f"Missing required column: {col}"
                })
    return failures

def validate_financial_integrity(df: pd.DataFrame, table_name: str) -> list[dict]:
    """DQ-03 & DQ-04: Validate financial relationships and balance sheet equation."""
    failures = []
    
    # DQ-03: Negative values where positive expected
    positive_cols = ['sales', 'total_assets', 'equity_capital']
    for col in positive_cols:
        if col in df.columns:
            invalid = df[df[col] < 0]
            for _, row in invalid.iterrows():
                failures.append({
                    "rule_id": "DQ-03",
                    "severity": "HIGH",
                    "table": table_name,
                    "record_id": f"{row.get('company_id')}_{row.get('year', '')}",
                    "details": f"Negative value in {col}: {row[col]}"
                })

    # DQ-04: Assets = Liabilities imbalance check (> 1% tolerance)
    if 'total_assets' in df.columns and 'total_liabilities' in df.columns:
        valid_assets = df[df['total_assets'] > 0]
        diff = (valid_assets['total_assets'] - valid_assets['total_liabilities']).abs() / valid_assets['total_assets']
        imbalanced = valid_assets[diff >= 0.01]
        for _, row in imbalanced.iterrows():
            failures.append({
                "rule_id": "DQ-04",
                "severity": "HIGH",
                "table": table_name,
                "record_id": f"{row.get('company_id')}_{row.get('year')}",
                "details": "Assets and Liabilities balance mismatch >= 1%"
            })

    return failures
