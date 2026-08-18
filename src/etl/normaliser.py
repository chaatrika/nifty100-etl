import re

def normalize_ticker(raw_ticker: str) -> str:
    """Removes special characters, spaces, and returns uppercase ticker."""
    if not raw_ticker or not isinstance(raw_ticker, str):
        return ""
    clean_ticker = re.sub(r'[^A-Za-z0-9]', '', raw_ticker)
    return clean_ticker.upper()

def normalize_year(raw_year: str | int) -> int:
    """Extracts 4-digit fiscal year from text, 2-digit years, or numeric input."""
    raw_str = str(raw_year).strip()
    
    # Direct 4-digit check
    if raw_str.isdigit() and len(raw_str) == 4:
        return int(raw_str)
    
    # 4-digit match (e.g., FY2022, 2020-21)
    match_4digit = re.search(r'(20\d{2}|19\d{2})', raw_str)
    if match_4digit:
        return int(match_4digit.group(1))
    
    # 2-digit year match (e.g., FY-18, FY18)
    match_2digit = re.search(r'(?:FY|CY)?[-_ ]?(\d{2})$', raw_str, re.IGNORECASE)
    if match_2digit:
        yy = int(match_2digit.group(1))
        return 2000 + yy if yy < 50 else 1900 + yy
        
    raise ValueError(f"Invalid year format: {raw_year}")
