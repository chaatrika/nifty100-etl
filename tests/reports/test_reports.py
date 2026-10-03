import os

import pytest

pypdf = pytest.importorskip("pypdf")

from src.reports import portfolio, sector_report, tearsheet
from src.reports.common import load_bundle


@pytest.fixture(scope="module")
def bundle():
    return load_bundle()


@pytest.mark.parametrize("ticker", ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"])
def test_tearsheet_is_two_pages_and_big_enough(ticker, bundle, tmp_path):
    path = tearsheet.make_tearsheet(ticker, bundle, str(tmp_path))
    assert len(pypdf.PdfReader(path).pages) == 2
    assert os.path.getsize(path) >= 30 * 1024


def test_short_history_company_gets_tearsheet(tmp_path):
    # JIOFIN has only 2 years of data: it still gets a 2-page tearsheet (with a limited-history note)
    files, skipped = tearsheet.run_batch(["JIOFIN"], str(tmp_path))
    assert skipped == [] and len(files) == 1
    assert len(pypdf.PdfReader(files[0]).pages) == 2
    assert os.path.getsize(files[0]) >= 30 * 1024


def test_unknown_ticker_is_skipped(tmp_path):
    files, skipped = tearsheet.run_batch(["ZZZZ"], str(tmp_path))
    assert files == [] and skipped[0][0] == "ZZZZ"


def test_eleven_sector_reports(tmp_path):
    files = sector_report.run_batch(str(tmp_path))
    assert len(files) == 11
    assert any("Conglomerates_Other" in f for f in files)


def test_sector_pdf(bundle, tmp_path):
    path = sector_report.make_sector_pdf("Information Technology", bundle, str(tmp_path))
    assert os.path.exists(path) and len(pypdf.PdfReader(path).pages) >= 1


def test_trend_rules():
    assert portfolio.trend(11, 10, True) == "up"
    assert portfolio.trend(9, 10, True) == "down"
    assert portfolio.trend(10.1, 10, True) == "flat"        # within 2%
    assert portfolio.trend(0.4, 0.5, False) == "up"         # lower D/E is better
    assert portfolio.trend(None, 5, True) is None
