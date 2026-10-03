"""Normalisation helpers for the Nifty 100 ETL pipeline.

normalize_year(): standardises a variety of raw year labels ('Mar-23',
'FY24', 'Dec-22', 2023, '2023-03', ...) into 'YYYY-MM' format.
normalize_ticker(): strips/upper-cases an NSE ticker string.
"""

from __future__ import annotations

import re
from typing import Optional

_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    "january": "01", "february": "02", "march": "03", "april": "04",
    "june": "06", "july": "07", "august": "08", "september": "09",
    "october": "10", "november": "11", "december": "12",
}

_ALREADY_NORMALISED = re.compile(r"^\d{4}-\d{2}$")
_MON_YY = re.compile(r"^([A-Za-z]+)[\s\-]?(\d{2,4})$")
_FY = re.compile(r"^FY[\s\-]?(\d{2,4})$", re.IGNORECASE)
_BARE_YEAR = re.compile(r"^\d{4}$")


def normalize_year(raw) -> Optional[str]:
    """Return 'YYYY-MM' for a raw year label, or None if unparseable (PARSE_ERROR)."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None

    # Already normalised: 2023-03
    if _ALREADY_NORMALISED.match(s):
        return s

    # Bare 4-digit year -> assume March FY close
    if _BARE_YEAR.match(s):
        return f"{s}-03"

    # FY23 / FY 23 / FY2023
    m = _FY.match(s)
    if m:
        yy = m.group(1)
        year = _expand_year(yy)
        return f"{year}-03"

    # Mon-YY / Mon YY / Month-YYYY  e.g. Mar-23, Mar 23, March-2023, Dec-22
    m = _MON_YY.match(s.replace(",", ""))
    if m:
        mon_raw, yy = m.group(1).lower(), m.group(2)
        month = _MONTH_MAP.get(mon_raw)
        if month is None:
            return None
        year = _expand_year(yy)
        return f"{year}-{month}"

    return None  # PARSE_ERROR


def _expand_year(yy: str) -> str:
    """Expand a 2-digit year to 4 digits (assume 2000s); pass through 4-digit years."""
    if len(yy) == 4:
        return yy
    n = int(yy)
    return f"20{n:02d}"


def normalize_ticker(raw) -> Optional[str]:
    """Strip whitespace and upper-case an NSE ticker. Returns None if out of length range (2-12)."""
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if not s or not (2 <= len(s) <= 12):
        return None
    return s
