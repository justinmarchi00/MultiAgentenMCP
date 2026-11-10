from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def data_directory() -> Path:
    configured = os.getenv("ORDERFLOW_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "data"


def load_json(filename: str) -> dict[str, Any]:
    path = data_directory() / filename
    if not path.is_file():
        raise FileNotFoundError(f"Testdatendatei nicht gefunden: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def list_customers() -> dict[str, Any]:
    return load_json("customers.json")


def list_products() -> dict[str, Any]:
    return load_json("products.json")


def list_capacity() -> dict[str, Any]:
    return load_json("capacity.json")


def list_suppliers() -> dict[str, Any]:
    return load_json("suppliers.json")

