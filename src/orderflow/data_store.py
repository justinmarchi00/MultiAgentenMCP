from __future__ import annotations

import json
import os
import re
from copy import deepcopy
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


def save_json(filename: str, data: dict[str, Any]) -> None:
    """Speichert Testdaten atomar, damit die Demo-Dateien konsistent bleiben."""
    path = data_directory() / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary_path.replace(path)


def _normalise_identifier(identifier: str, prefix: str) -> str:
    value = identifier.strip().upper()
    if not re.fullmatch(rf"{prefix}[A-Z0-9_-]{{1,29}}", value):
        raise ValueError(
            f"Die Kennung muss mit {prefix} beginnen und darf nur Buchstaben, "
            "Zahlen, Unterstriche oder Bindestriche enthalten."
        )
    return value


def add_customer(
    customer_id: str,
    *,
    name: str,
    credit_status: str,
    country: str,
    payment_terms_days: int,
) -> str:
    """Legt einen neuen Demo-Kunden im simulierten CRM an."""
    identifier = _normalise_identifier(customer_id, "C")
    cleaned_name = name.strip()
    if len(cleaned_name) < 2:
        raise ValueError("Bitte einen aussagekräftigen Kundennamen eingeben.")
    if credit_status not in {"freigegeben", "gesperrt", "in Prüfung"}:
        raise ValueError("Der Bonitätsstatus ist ungültig.")
    if not 0 <= payment_terms_days <= 365:
        raise ValueError("Das Zahlungsziel muss zwischen 0 und 365 Tagen liegen.")

    customers = deepcopy(list_customers())
    if identifier in customers:
        raise ValueError(f"Der Kunde {identifier} existiert bereits.")
    customers[identifier] = {
        "name": cleaned_name,
        "credit_status": credit_status,
        "country": country.strip().upper() or "DE",
        "payment_terms_days": int(payment_terms_days),
    }
    save_json("customers.json", customers)
    return identifier


def update_customer(
    customer_id: str,
    *,
    name: str,
    credit_status: str,
    country: str,
    payment_terms_days: int,
) -> str:
    """Aktualisiert einen bestehenden Demo-Kunden."""
    identifier = _normalise_identifier(customer_id, "C")
    cleaned_name = name.strip()
    if len(cleaned_name) < 2:
        raise ValueError("Bitte einen aussagekräftigen Kundennamen eingeben.")
    if credit_status not in {"freigegeben", "gesperrt", "in Prüfung"}:
        raise ValueError("Der Bonitätsstatus ist ungültig.")
    if not 0 <= payment_terms_days <= 365:
        raise ValueError("Das Zahlungsziel muss zwischen 0 und 365 Tagen liegen.")

    customers = deepcopy(list_customers())
    if identifier not in customers:
        raise ValueError(f"Der Kunde {identifier} wurde nicht gefunden.")
    customers[identifier] = {
        "name": cleaned_name,
        "credit_status": credit_status,
        "country": country.strip().upper() or "DE",
        "payment_terms_days": int(payment_terms_days),
    }
    save_json("customers.json", customers)
    return identifier


def delete_customer(customer_id: str) -> str:
    """Entfernt einen Demo-Kunden, schützt aber den letzten Datensatz."""
    identifier = _normalise_identifier(customer_id, "C")
    customers = deepcopy(list_customers())
    if identifier not in customers:
        raise ValueError(f"Der Kunde {identifier} wurde nicht gefunden.")
    if len(customers) <= 1:
        raise ValueError("Der letzte Kunde kann nicht gelöscht werden.")
    customers.pop(identifier)
    save_json("customers.json", customers)
    return identifier


def add_product(
    product_id: str,
    *,
    name: str,
    stock: int,
    unit_price: float,
    weekly_capacity: int,
    setup_days: int,
    working_days_per_week: int = 5,
    supplier: str = "",
    maximum_quantity: int = 0,
    lead_time_days: int = 0,
) -> str:
    """Legt Produkt-, Kapazitäts- und optionale Lieferantendaten gemeinsam an."""
    identifier = _normalise_identifier(product_id, "P")
    cleaned_name = name.strip()
    if len(cleaned_name) < 2:
        raise ValueError("Bitte einen aussagekräftigen Produktnamen eingeben.")
    if stock < 0 or unit_price < 0 or weekly_capacity < 0 or setup_days < 0:
        raise ValueError("Bestand, Preis, Kapazität und Rüstzeit dürfen nicht negativ sein.")
    if not 1 <= working_days_per_week <= 7:
        raise ValueError("Die Arbeitstage pro Woche müssen zwischen 1 und 7 liegen.")

    products = deepcopy(list_products())
    capacities = deepcopy(list_capacity())
    suppliers = deepcopy(list_suppliers())
    if identifier in products:
        raise ValueError(f"Das Produkt {identifier} existiert bereits.")

    products[identifier] = {
        "name": cleaned_name,
        "stock": int(stock),
        "unit_price": round(float(unit_price), 2),
        "currency": "EUR",
    }
    capacities[identifier] = {
        "weekly_capacity": int(weekly_capacity),
        "setup_days": int(setup_days),
        "working_days_per_week": int(working_days_per_week),
    }
    if supplier.strip():
        if maximum_quantity <= 0 or lead_time_days <= 0:
            raise ValueError(
                "Für einen Lieferanten müssen Bezugsmenge und Lieferzeit größer als null sein."
            )
        suppliers[identifier] = {
            "supplier": supplier.strip(),
            "maximum_quantity": int(maximum_quantity),
            "lead_time_days": int(lead_time_days),
        }

    save_json("products.json", products)
    save_json("capacity.json", capacities)
    save_json("suppliers.json", suppliers)
    return identifier


def update_product(
    product_id: str,
    *,
    name: str,
    stock: int,
    unit_price: float,
    weekly_capacity: int,
    setup_days: int,
    working_days_per_week: int = 5,
    supplier: str = "",
    maximum_quantity: int = 0,
    lead_time_days: int = 0,
) -> str:
    """Aktualisiert ein bestehendes Demo-Produkt und seine abhängigen Stammdaten."""
    identifier = _normalise_identifier(product_id, "P")
    cleaned_name = name.strip()
    if len(cleaned_name) < 2:
        raise ValueError("Bitte einen aussagekräftigen Produktnamen eingeben.")
    if stock < 0 or unit_price < 0 or weekly_capacity < 0 or setup_days < 0:
        raise ValueError("Bestand, Preis, Kapazität und Rüstzeit dürfen nicht negativ sein.")
    if not 1 <= working_days_per_week <= 7:
        raise ValueError("Die Arbeitstage pro Woche müssen zwischen 1 und 7 liegen.")

    products = deepcopy(list_products())
    capacities = deepcopy(list_capacity())
    suppliers = deepcopy(list_suppliers())
    if identifier not in products:
        raise ValueError(f"Das Produkt {identifier} wurde nicht gefunden.")

    products[identifier] = {
        "name": cleaned_name,
        "stock": int(stock),
        "unit_price": round(float(unit_price), 2),
        "currency": "EUR",
    }
    capacities[identifier] = {
        "weekly_capacity": int(weekly_capacity),
        "setup_days": int(setup_days),
        "working_days_per_week": int(working_days_per_week),
    }
    if supplier.strip():
        if maximum_quantity <= 0 or lead_time_days <= 0:
            raise ValueError(
                "Für einen Lieferanten müssen Bezugsmenge und Lieferzeit größer als null sein."
            )
        suppliers[identifier] = {
            "supplier": supplier.strip(),
            "maximum_quantity": int(maximum_quantity),
            "lead_time_days": int(lead_time_days),
        }
    else:
        suppliers.pop(identifier, None)

    save_json("products.json", products)
    save_json("capacity.json", capacities)
    save_json("suppliers.json", suppliers)
    return identifier


def delete_product(product_id: str) -> str:
    """Entfernt ein Demo-Produkt einschließlich Kapazitäts- und Lieferantendaten."""
    identifier = _normalise_identifier(product_id, "P")
    products = deepcopy(list_products())
    capacities = deepcopy(list_capacity())
    suppliers = deepcopy(list_suppliers())
    if identifier not in products:
        raise ValueError(f"Das Produkt {identifier} wurde nicht gefunden.")
    if len(products) <= 1:
        raise ValueError("Das letzte Produkt kann nicht gelöscht werden.")

    products.pop(identifier)
    capacities.pop(identifier, None)
    suppliers.pop(identifier, None)
    save_json("products.json", products)
    save_json("capacity.json", capacities)
    save_json("suppliers.json", suppliers)
    return identifier


def list_customers() -> dict[str, Any]:
    return load_json("customers.json")


def list_products() -> dict[str, Any]:
    return load_json("products.json")


def list_capacity() -> dict[str, Any]:
    return load_json("capacity.json")


def list_suppliers() -> dict[str, Any]:
    return load_json("suppliers.json")

