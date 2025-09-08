"""Initial schema from db/schema.sql

Revision ID: 000_initial_schema
Revises: 
Create Date: 2025-09-08 00:00:00.000000

"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "000_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _load_and_sanitize_schema_sql() -> List[str]:
    """
    Load db/schema.sql, strip unsupported commands and schema qualifiers, and
    split into executable statements. Make inserts idempotent to support existing DBs.
    """
    # Determine project root from this file: migrations/versions/<this_file>
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]
    schema_path = project_root / "db" / "schema.sql"

    if not schema_path.exists():
        # Fallback for alternate location used by docker-entrypoint-initdb.d
        alt_path = project_root / "db" / "docker-entrypoint-initdb.d" / "schema.sql"
        if alt_path.exists():
            schema_path = alt_path
        else:
            raise FileNotFoundError(f"Could not find schema.sql at {schema_path} or {alt_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql_text = f.read()

    # Remove MySQL client/session directives and explicit schema usage
    processed_lines: List[str] = []
    for raw_line in sql_text.splitlines():
        line = raw_line.strip()
        # Skip comments and session directives
        if not line or line.startswith("--"):
            continue
        if line.upper().startswith("SET "):
            continue
        if line.upper().startswith("USE "):
            continue
        if line.upper().startswith("START TRANSACTION"):
            continue
        if line.upper().startswith("COMMIT"):
            continue
        if line.upper().startswith("CREATE SCHEMA ") or line.upper().startswith("CREATE DATABASE "):
            continue
        # Remove explicit schema qualifiers like `online_shop`.
        line = line.replace("`online_shop`.", "")
        # Make inserts idempotent to avoid duplicate key errors on existing datasets
        if line.upper().startswith("INSERT INTO "):
            line = line.replace("INSERT INTO ", "INSERT IGNORE INTO ", 1)
        processed_lines.append(line)

    sanitized = "\n".join(processed_lines)

    # Split on semicolons while keeping structure simple. This assumes no
    # embedded semicolons in strings (true for our file).
    statements = [stmt.strip() for stmt in sanitized.split(";")]
    # Filter empties
    statements = [s for s in statements if s]
    return statements


def upgrade() -> None:
    connection = op.get_bind()

    statements = _load_and_sanitize_schema_sql()

    # Execute each statement individually to better surface errors
    for stmt in statements:
        connection.exec_driver_sql(stmt)


def downgrade() -> None:
    connection = op.get_bind()

    # Drop in dependency-safe order (children/junction tables first)
    tables_in_drop_order = [
        # Junction/order tables and dependents
        "liste_au_produse_ordered",
        "liste_au_categorii",
        "liste_au_tipuri_livrare",
        "comenzi_au_produse",
        "product_images",
        "secondary_images",
        "product_overrides",
        # Main tables with FKs
        "comenzi",
        "produse",
        "liste",
        # Reference tables
        "category",
        "unitati",
        "orare_livrari",
        "modalitati_de_plata",
        "tipuri_livrare",
        "business_details",
        "admins",
    ]

    for table_name in tables_in_drop_order:
        connection.exec_driver_sql(f"DROP TABLE IF EXISTS `{table_name}`")
