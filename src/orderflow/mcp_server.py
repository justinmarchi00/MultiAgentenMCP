from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from mcp.server import MCPServer

from orderflow.data_store import list_capacity, list_customers, list_products, list_suppliers

mcp = MCPServer("OrderFlow BPM Server")


@mcp.tool()
def get_customer(customer_id: str) -> dict[str, Any]:
    """Liefert Stammdaten und Bonitätsstatus eines Kunden."""
    customer = list_customers().get(customer_id)
    if customer is None:
        return {
            "found": False,
            "customer_id": customer_id,
            "error": "Kunde wurde nicht gefunden.",
        }
    return {"found": True, "customer_id": customer_id, **customer}


@mcp.tool()
def check_stock(product_id: str, quantity: int) -> dict[str, Any]:
    """Prüft Lagerbestand und Fehlmenge für eine Auftragsposition."""
    if quantity <= 0:
        return {"available": False, "error": "Die Menge muss größer als null sein."}

    product = list_products().get(product_id)
    if product is None:
        return {
            "available": False,
            "product_id": product_id,
            "error": "Produkt wurde nicht gefunden.",
        }

    stock = int(product["stock"])
    return {
        "product_id": product_id,
        "product_name": product["name"],
        "available": stock >= quantity,
        "requested_quantity": quantity,
        "current_stock": stock,
        "missing_quantity": max(0, quantity - stock),
    }


@mcp.tool()
def check_capacity(product_id: str, quantity: int) -> dict[str, Any]:
    """Prüft, ob eine fehlende Menge innerhalb einer Woche produziert werden kann."""
    if quantity <= 0:
        return {
            "possible": True,
            "required_quantity": 0,
            "weekly_capacity": 0,
            "production_days": 0,
        }

    capacity = list_capacity().get(product_id)
    if capacity is None:
        return {
            "possible": False,
            "product_id": product_id,
            "error": "Keine Kapazitätsdaten vorhanden.",
        }

    weekly_capacity = int(capacity["weekly_capacity"])
    return {
        "product_id": product_id,
        "possible": quantity <= weekly_capacity,
        "required_quantity": quantity,
        "weekly_capacity": weekly_capacity,
        "production_days": int(capacity["production_days"]),
    }


@mcp.tool()
def check_procurement(product_id: str, quantity: int) -> dict[str, Any]:
    """Prüft eine externe Beschaffungsoption für eine noch offene Menge."""
    if quantity <= 0:
        return {
            "required": False,
            "possible": True,
            "required_quantity": 0,
            "lead_time_days": 0,
        }

    supplier = list_suppliers().get(product_id)
    if supplier is None:
        return {
            "required": True,
            "possible": False,
            "product_id": product_id,
            "required_quantity": quantity,
            "error": "Keine Lieferantendaten vorhanden.",
        }

    maximum_quantity = int(supplier["maximum_quantity"])
    return {
        "required": True,
        "possible": quantity <= maximum_quantity,
        "product_id": product_id,
        "supplier": supplier["supplier"],
        "required_quantity": quantity,
        "maximum_quantity": maximum_quantity,
        "lead_time_days": int(supplier["lead_time_days"]),
    }


@mcp.tool()
def calculate_price(product_id: str, quantity: int) -> dict[str, Any]:
    """Berechnet Netto-Gesamtpreis und einen einfachen Mengenrabatt."""
    product = list_products().get(product_id)
    if product is None:
        return {"product_id": product_id, "error": "Produkt wurde nicht gefunden."}
    if quantity <= 0:
        return {"product_id": product_id, "error": "Die Menge muss größer als null sein."}

    unit_price = float(product["unit_price"])
    discount_rate = 0.10 if quantity >= 50 else 0.05 if quantity >= 20 else 0.0
    subtotal = unit_price * quantity
    total = subtotal * (1 - discount_rate)

    return {
        "product_id": product_id,
        "currency": product.get("currency", "EUR"),
        "unit_price": round(unit_price, 2),
        "quantity": quantity,
        "subtotal": round(subtotal, 2),
        "discount_rate": discount_rate,
        "total_price": round(total, 2),
    }


@mcp.tool()
def calculate_delivery_date(
    requested_date: str,
    stock_available: bool,
    production_days: int = 0,
    planning_date: str | None = None,
) -> dict[str, Any]:
    """Ermittelt aus Wunschdatum und Produktionsdauer einen zugesagten Liefertermin."""
    try:
        requested = date.fromisoformat(requested_date)
        planning = date.fromisoformat(planning_date) if planning_date else date.today()
    except ValueError:
        return {"error": "Datum muss im ISO-Format YYYY-MM-DD übergeben werden."}

    earliest = planning if stock_available else planning + timedelta(days=max(0, production_days))
    promised = max(requested, earliest)
    return {
        "requested_date": requested.isoformat(),
        "planning_date": planning.isoformat(),
        "stock_available": stock_available,
        "production_days": max(0, production_days),
        "promised_date": promised.isoformat(),
        "requested_date_met": promised <= requested,
    }


if __name__ == "__main__":
    raise SystemExit(
        "Bitte mit 'mcp dev src/orderflow/mcp_server.py' oder "
        "'mcp run src/orderflow/mcp_server.py --transport streamable-http' starten."
    )

