.PHONY: env install schema load test DQ clean

env:
    python -m venv venv

install:
    pip install -r requirements.txt

schema:
    sqlite3 nifty100.db < db/schema.sql

load:
    python -m src.etl.loader

test:
    pytest tests/ -v --cov=src

clean:
    rm -f nifty100.db output/*.csv
