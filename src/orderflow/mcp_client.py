from __future__ import annotations

import json
from typing import Any

from mcp import Client

from orderflow.mcp_server import mcp
from orderflow.models import OrderRequest


def _structured_result(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured

    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if not text:
            continue
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise RuntimeError("Der MCP-Server hat kein strukturiertes Ergebnis geliefert.")


async def call_tool(client: Client, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    result = await client.call_tool(name, arguments)
    return _structured_result(result)


def _select_fulfillment(
    stock: dict[str, Any],
    capacity: dict[str, Any] | None,
    procurement: dict[str, Any] | None,
) -> dict[str, Any]:
    """Wählt genau einen widerspruchsfreien Erfüllungsweg für den Auftrag."""
    if stock.get("available", False):
        return {
            "possible": True,
            "method": "stock",
            "duration_days": 0,
            "reason": "Die vollständige Auftragsmenge liegt auf Lager.",
        }

    if capacity and capacity.get("possible") and capacity.get("within_week_capacity"):
        return {
            "possible": True,
            "method": "production",
            "duration_days": int(capacity.get("production_days", 0)),
            "reason": "Die Fehlmenge kann innerhalb der Wochenkapazität produziert werden.",
        }

    if procurement and procurement.get("possible"):
        return {
            "possible": True,
            "method": "procurement",
            "duration_days": int(procurement.get("lead_time_days", 0)),
            "reason": "Die vollständige Fehlmenge kann extern beschafft werden.",
        }

    if capacity and capacity.get("possible"):
        return {
            "possible": True,
            "method": "production",
            "duration_days": int(capacity.get("production_days", 0)),
            "reason": (
                "Die Fehlmenge benötigt mehr als eine Produktionswoche, kann aber "
                "vollständig intern produziert werden."
            ),
        }

    return {
        "possible": False,
        "method": "manual",
        "duration_days": None,
        "reason": "Kein vollständiger Erfüllungsweg ist automatisch planbar.",
    }


async def evaluate_order_via_mcp(order: OrderRequest) -> dict[str, Any]:
    """Ruft alle benötigten ERP-Simulationen über einen MCP-Client auf."""
    async with Client(mcp) as client:
        customer = await call_tool(client, "get_customer", {"customer_id": order.customer_id})
        stock = await call_tool(
            client,
            "check_stock",
            {"product_id": order.product_id, "quantity": order.quantity},
        )
        price = await call_tool(
            client,
            "calculate_price",
            {"product_id": order.product_id, "quantity": order.quantity},
        )

        missing_quantity = int(stock.get("missing_quantity", 0))
        capacity = None
        procurement = None
        if missing_quantity > 0:
            capacity = await call_tool(
                client,
                "check_capacity",
                {"product_id": order.product_id, "quantity": missing_quantity},
            )

            if not capacity.get("within_week_capacity", False):
                procurement = await call_tool(
                    client,
                    "check_procurement",
                    {"product_id": order.product_id, "quantity": missing_quantity},
                )

        fulfillment = _select_fulfillment(stock, capacity, procurement)
        delivery = await call_tool(
            client,
            "calculate_delivery_date",
            {
                "requested_date": order.requested_date.isoformat(),
                "stock_available": bool(stock.get("available", False)),
                "production_days": int(fulfillment.get("duration_days") or 0),
                "fulfillment_possible": bool(fulfillment["possible"]),
                "fulfillment_method": str(fulfillment["method"]),
            },
        )
        delivery["fulfillment_reason"] = fulfillment["reason"]

    return {
        "customer": customer,
        "stock": stock,
        "capacity": capacity,
        "procurement": procurement,
        "price": price,
        "delivery": delivery,
    }

