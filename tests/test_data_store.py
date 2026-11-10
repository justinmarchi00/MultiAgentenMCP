import json

from orderflow.data_store import (
    add_customer,
    add_product,
    delete_customer,
    delete_product,
    list_capacity,
    list_customers,
    list_products,
    list_suppliers,
    update_customer,
    update_product,
)


def write_json(path, content: dict) -> None:
    path.write_text(json.dumps(content), encoding="utf-8")


def test_demo_master_data_can_be_added(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ORDERFLOW_DATA_DIR", str(tmp_path))
    write_json(
        tmp_path / "customers.json",
        {
            "C100": {
                "name": "Basiskunde",
                "credit_status": "freigegeben",
                "country": "DE",
                "payment_terms_days": 30,
            }
        },
    )
    write_json(
        tmp_path / "products.json",
        {"P100": {"name": "Basisprodukt", "stock": 1, "unit_price": 1, "currency": "EUR"}},
    )
    write_json(
        tmp_path / "capacity.json",
        {"P100": {"weekly_capacity": 1, "setup_days": 0, "working_days_per_week": 5}},
    )
    write_json(tmp_path / "suppliers.json", {})

    customer_id = add_customer(
        "c900",
        name="Demo GmbH",
        credit_status="freigegeben",
        country="de",
        payment_terms_days=30,
    )
    product_id = add_product(
        "p900",
        name="Demoteil",
        stock=12,
        unit_price=19.95,
        weekly_capacity=50,
        setup_days=1,
        supplier="Demo Lieferant",
        maximum_quantity=100,
        lead_time_days=4,
    )

    assert customer_id == "C900"
    assert list_customers()["C900"]["name"] == "Demo GmbH"
    assert product_id == "P900"
    assert list_products()["P900"]["unit_price"] == 19.95

    update_customer(
        "C900",
        name="Demo AG",
        credit_status="in Prüfung",
        country="AT",
        payment_terms_days=14,
    )
    assert list_customers()["C900"]["name"] == "Demo AG"
    assert list_customers()["C900"]["credit_status"] == "in Prüfung"

    delete_customer("C900")
    assert "C900" not in list_customers()

    update_product(
        "P900",
        name="Demoteil Plus",
        stock=25,
        unit_price=24.5,
        weekly_capacity=80,
        setup_days=2,
        supplier="Neuer Lieferant",
        maximum_quantity=200,
        lead_time_days=3,
    )

    assert list_products()["P900"]["name"] == "Demoteil Plus"
    assert list_capacity()["P900"]["setup_days"] == 2
    assert list_suppliers()["P900"]["lead_time_days"] == 3

    delete_product("P900")
    assert "P900" not in list_products()
    assert "P900" not in list_capacity()
    assert "P900" not in list_suppliers()
