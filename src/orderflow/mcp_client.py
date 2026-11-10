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

            if not capacity.get("possible", False):
                procurement = await call_tool(
                    client,
                    "check_procurement",
                    {"product_id": order.product_id, "quantity": missing_quantity},
                )

        production_days = int((capacity or {}).get("production_days", 0))
        procurement_days = int((procurement or {}).get("lead_time_days", 0))
        delivery = await call_tool(
            client,
            "calculate_delivery_date",
            {
                "requested_date": order.requested_date.isoformat(),
                "stock_available": bool(stock.get("available", False)),
                "production_days": max(production_days, procurement_days),
            },
        )

    return {
        "customer": customer,
        "stock": stock,
        "capacity": capacity,
        "procurement": procurement,
        "price": price,
        "delivery": delivery,
    }

