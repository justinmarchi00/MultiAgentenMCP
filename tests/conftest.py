import json

import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def isolated_demo_data(tmp_path, monkeypatch) -> None:
    """Jeder Test erhält reproduzierbare Stammdaten statt veränderlicher Demo-Daten."""
    monkeypatch.setenv("ORDERFLOW_DATA_DIR", str(tmp_path))
    fixtures = {
        "customers.json": {
            "C100": {
                "name": "Muster GmbH",
                "credit_status": "freigegeben",
                "country": "DE",
                "payment_terms_days": 30,
            },
            "C200": {
                "name": "Test AG",
                "credit_status": "gesperrt",
                "country": "DE",
                "payment_terms_days": 14,
            },
            "C300": {
                "name": "Prüfkunde KG",
                "credit_status": "in Prüfung",
                "country": "AT",
                "payment_terms_days": 30,
            },
        },
        "products.json": {
            "P100": {
                "name": "Industriepumpe",
                "stock": 25,
                "unit_price": 450.0,
                "currency": "EUR",
            },
            "P300": {
                "name": "Drucksensor",
                "stock": 100,
                "unit_price": 89.9,
                "currency": "EUR",
            },
            "P400": {
                "name": "Industriekeilriemen",
                "stock": 0,
                "unit_price": 249.0,
                "currency": "EUR",
            },
            "P500": {
                "name": "Zahnrad",
                "stock": 20,
                "unit_price": 40.0,
                "currency": "EUR",
            },
        },
        "capacity.json": {
            "P100": {
                "weekly_capacity": 40,
                "setup_days": 1,
                "working_days_per_week": 5,
            },
            "P300": {
                "weekly_capacity": 150,
                "setup_days": 2,
                "working_days_per_week": 5,
            },
            "P400": {
                "weekly_capacity": 0,
                "setup_days": 2,
                "working_days_per_week": 5,
            },
            "P500": {
                "weekly_capacity": 250,
                "setup_days": 1,
                "working_days_per_week": 5,
            },
        },
        "suppliers.json": {
            "P100": {
                "supplier": "Pumpenwerke Nord GmbH",
                "maximum_quantity": 100,
                "lead_time_days": 10,
            },
            "P400": {
                "supplier": "Continental",
                "maximum_quantity": 30,
                "lead_time_days": 1,
            },
            "P500": {
                "supplier": "Zahnrad AG",
                "maximum_quantity": 100,
                "lead_time_days": 1,
            },
        },
    }
    for filename, content in fixtures.items():
        (tmp_path / filename).write_text(
            json.dumps(content, ensure_ascii=False), encoding="utf-8"
        )

