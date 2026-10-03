.PHONY: api report load ratios verify screener peers radar peer-report valuation dashboard nlp cashflow tearsheets sector-reports portfolio test test-kpi clean
load:
	python3 src/etl/loader.py

ratios:
	python3 -m src.analytics.run_ratio_engine

verify:
	python3 -m src.analytics.verify_sprint2

screener:
	python3 -m src.screener.run_screener

peers:
	python3 -m src.analytics.peer

radar:
	python3 -m src.analytics.radar

peer-report:
	python3 -m src.analytics.peer_report

valuation:
	python3 -m src.analytics.valuation

dashboard:
	streamlit run src/dashboard/app.py --server.port 8501

api:
	python3 -m uvicorn src.api.main:app --port 8000

report: tearsheets sector-reports portfolio

nlp:
	python3 -m src.nlp.parser
	python3 -m src.nlp.pros_cons_generator

cashflow:
	python3 -m src.analytics.cashflow_intelligence
	python3 -m src.analytics.capital_report

tearsheets:
	python3 -m src.reports.tearsheet

sector-reports:
	python3 -m src.reports.sector_report

portfolio:
	python3 -m src.reports.portfolio

test:
	mkdir -p reports
	python3 -m pytest tests/ -q --html=reports/pytest_report.html --self-contained-html

test-kpi:
	python3 -m pytest tests/kpi -q

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete
