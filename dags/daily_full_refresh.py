"""Airflow DAG for the 6:00am daily full refresh into Postgres.

The DAG uses TaskFlow API plus TaskGroups to fan out ingestion per asset:
1) extract_and_load_stage: call asset-specific extractor and write to staging.
2) validate_stage: confirm staging row counts.
3) finalize_all: after all validations succeed, atomically swap stage -> raw.
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import pendulum
from airflow.decorators import dag, task, task_group
from airflow.utils.trigger_rule import TriggerRule

# Ensure local modules are importable when Airflow parses from the dags folder.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from src.db.postgres import count_rows, get_postgres_hook, load_rows_to_table, swap_stage_to_raw
from src.ingest.asset_config import ASSETS
from src.ingest.utils import load_callable_from_path


@dataclass(frozen=True)
class Asset:
    """Configuration for an ingestible asset."""

    name: str
    python_callable: str
    target_table: str
    staging_table: str


SCHEDULE_CRON = "0 6 * * *"
TIMEZONE = "America/Bogota"
DEFAULT_CONN_ID = "spread_eagle_postgres"


@dag(
    schedule=SCHEDULE_CRON,
    start_date=pendulum.datetime(2024, 1, 1, tz=TIMEZONE),
    catchup=False,
    max_active_runs=1,
    tags=["full_refresh", "postgres", "ingestion"],
)
def daily_full_refresh():
    """Orchestrates full-refresh ingestion into Postgres staging then raw."""

    @task
    def extract_and_load_stage(asset: Asset) -> int:
        """Run the asset extractor and load results into staging.

        Returns the number of rows loaded into staging.
        """

        hook = get_postgres_hook(conn_id=DEFAULT_CONN_ID)
        start = time.perf_counter()

        extractor = load_callable_from_path(asset.python_callable)
        rows: Iterable[Mapping[str, object]] = extractor()
        rows_list = list(rows)

        loaded = load_rows_to_table(
            hook=hook,
            table=asset.staging_table,
            rows=rows_list,
            truncate=True,
        )

        stage_count = count_rows(hook=hook, table=asset.staging_table)
        duration = time.perf_counter() - start

        logging.info(
            "Asset %s: extracted %s rows, loaded %s rows to %s, stage count=%s, runtime=%.2fs",
            asset.name,
            len(rows_list),
            loaded,
            asset.staging_table,
            stage_count,
            duration,
        )

        return stage_count

    @task
    def validate_stage(asset: Asset, upstream_row_count: int) -> int:
        """Validate staging table row counts."""

        hook = get_postgres_hook(conn_id=DEFAULT_CONN_ID)
        start = time.perf_counter()
        stage_count = count_rows(hook=hook, table=asset.staging_table)
        duration = time.perf_counter() - start

        logging.info(
            "Asset %s: upstream reported %s rows, staging has %s rows, runtime=%.2fs",
            asset.name,
            upstream_row_count,
            stage_count,
            duration,
        )

        if stage_count != upstream_row_count:
            raise ValueError(
                f"Staging row count mismatch for {asset.name}: {stage_count} vs expected {upstream_row_count}"
            )

        return stage_count

    @task(trigger_rule=TriggerRule.ALL_SUCCESS)
    def finalize_all(assets: list[Asset]) -> None:
        """Swap staged data into raw tables using single transactions per table."""

        hook = get_postgres_hook(conn_id=DEFAULT_CONN_ID)
        start_all = time.perf_counter()

        for asset in assets:
            start = time.perf_counter()
            swap_stage_to_raw(
                hook=hook,
                raw_table=asset.target_table,
                staging_table=asset.staging_table,
            )
            raw_count = count_rows(hook=hook, table=asset.target_table)
            stage_count = count_rows(hook=hook, table=asset.staging_table)
            duration = time.perf_counter() - start

            logging.info(
                "Finalize %s: swapped %s -> %s, raw count=%s, staging count=%s, runtime=%.2fs",
                asset.name,
                asset.staging_table,
                asset.target_table,
                raw_count,
                stage_count,
                duration,
            )

        logging.info("Finalize all assets runtime=%.2fs", time.perf_counter() - start_all)

    # Build TaskGroups per asset.
    validate_tasks = []
    asset_objects = [Asset(**asset_cfg) for asset_cfg in ASSETS]

    for asset in asset_objects:
        with task_group(group_id=f"{asset.name}_pipeline"):
            load = extract_and_load_stage(asset)
            validate = validate_stage(asset, upstream_row_count=load)
            load >> validate
            validate_tasks.append(validate)

    finalize_all(asset_objects) << validate_tasks


dag_instance = daily_full_refresh()


