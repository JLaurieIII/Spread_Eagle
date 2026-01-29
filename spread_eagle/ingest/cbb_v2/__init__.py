"""
CBB Ingest V2 - Complete College Basketball Data Ingestion Pipeline

This module provides:
- Full load and incremental (CDC) data loading
- Direct Postgres loading with upsert logic
- Single orchestrator for Airflow integration

Usage:
    # Full load all data
    python -m spread_eagle.ingest.cbb_v2.run_ingest --mode full --start_year 2022 --end_year 2025

    # Incremental load (recent data only)
    python -m spread_eagle.ingest.cbb_v2.run_ingest --mode incremental

    # Load specific datasets
    python -m spread_eagle.ingest.cbb_v2.run_ingest --mode full --datasets games,lines,team_stats
"""

__version__ = "2.0.0"
