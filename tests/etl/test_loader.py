import os
import sqlite3
import pandas as pd
import pytest
from src.etl.loader import initialize_database, log_audit_trail, log_validation_failures, load_sample_companies, main

def test_initialize_database(tmp_path):
    db_file = tmp_path / "test_nifty.db"
    schema_file = tmp_path / "schema.sql"
    schema_file.write_text("CREATE TABLE test_table (id INT);", encoding="utf-8")

    initialize_database(db_path=str(db_file), schema_path=str(schema_file))
    
    assert db_file.exists()
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table';")
    assert cursor.fetchone() is not None
    conn.close()

def test_log_audit_trail(tmp_path, monkeypatch):
    audit_file = tmp_path / "load_audit.csv"
    monkeypatch.setattr("src.etl.loader.AUDIT_LOG_PATH", str(audit_file))

    log_audit_trail("test_table", 10, "SUCCESS")
    assert audit_file.exists()
    
    df = pd.read_csv(str(audit_file))
    assert len(df) == 1
    assert df.iloc[0]["table_name"] == "test_table"

def test_log_validation_failures(tmp_path, monkeypatch):
    failures_file = tmp_path / "validation_failures.csv"
    monkeypatch.setattr("src.etl.loader.FAILURES_LOG_PATH", str(failures_file))

    failures = [{"rule_id": "DQ-01", "severity": "HIGH", "details": "Test failure"}]
    log_validation_failures(failures)
    assert failures_file.exists()

    # Empty list should do nothing
    log_validation_failures([])

def test_load_sample_companies_idempotent(tmp_path):
    db_file = tmp_path / "test_companies.db"
    initialize_database(db_path=str(db_file))
    
    # First load
    load_sample_companies(db_path=str(db_file))
    conn = sqlite3.connect(str(db_file))
    count1 = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    conn.close()
    assert count1 == 3

    # Second load (idempotent - should ignore duplicates without throwing error)
    load_sample_companies(db_path=str(db_file))
    conn = sqlite3.connect(str(db_file))
    count2 = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    conn.close()
    assert count2 == 3

def test_loader_execution():
    main()
    assert os.path.exists("nifty100.db")
    assert os.path.exists("output/load_audit.csv")