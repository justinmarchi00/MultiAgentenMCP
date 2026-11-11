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
    """Wählt den schnellsten vollständigen Erfüllungsweg für den Auftrag.

    Lagerware hat immer Vorrang, weil keine zusätzliche Bereitstellung notwendig ist.
    Bei einer Fehlmenge werden interne Produktion und externe Beschaffung unabhängig
    voneinander bewertet. Nur Wege, die die *gesamte* Fehlmenge abdecken, kommen in
    Betracht. Bei gleicher Dauer wird die interne Produktion bevorzugt, damit die
    Entscheidung reproduzierbar bleibt und keine unnötige Fremdbeschaffung entsteht.
    """
    def duration_text(value: int) -> str:
        unit = "Arbeitstag" if value == 1 else "Arbeitstage"
        return f"{value} {unit}"

    if stock.get("available", False):
        return {
            "possible": True,
            "method": "stock",
            "duration_days": 0,
            "reason": "Die vollständige Auftragsmenge liegt auf Lager.",
            "evaluated_routes": [{"method": "stock", "duration_days": 0}],
        }

    candidates: list[dict[str, Any]] = []
    if capacity and capacity.get("possible"):
        candidates.append(
            {
                "method": "production",
                "duration_days": max(0, int(capacity.get("production_days", 0))),
            }
        )
    if procurement and procurement.get("possible"):
        candidates.append(
            {
                "method": "procurement",
                "duration_days": max(0, int(procurement.get("lead_time_days", 0))),
            }
        )

    if candidates:
        # Bei gleicher Dauer ist die interne Produktion die stabile Standardregel.
        priority = {"production": 0, "procurement": 1}
        chosen = min(
            candidates,
            key=lambda route: (route["duration_days"], priority[route["method"]]),
        )
        production = next(
            (route for route in candidates if route["method"] == "production"), None
        )
        procurement_route = next(
            (route for route in candidates if route["method"] == "procurement"), None
        )

        if production and procurement_route:
            production_days = production["duration_days"]
            procurement_days = procurement_route["duration_days"]
            if chosen["method"] == "procurement":
                reason = (
                    "Die externe Beschaffung deckt die vollständige Fehlmenge ab. "
                    f"Ihre Dauer beträgt {duration_text(procurement_days)}; die interne "
                    f"Produktion benötigt {duration_text(production_days)}. Daher wird die "
                    "schnellere externe Beschaffung gewählt."
                )
            elif production_days == procurement_days:
                reason = (
                    "Interne Produktion und externe Beschaffung benötigen jeweils "
                    f"{duration_text(production_days)}. Bei Gleichstand wird die interne "
                    "Produktion bevorzugt."
                )
            else:
                reason = (
                    "Die interne Produktion deckt die vollständige Fehlmenge ab. "
                    f"Ihre Dauer beträgt {duration_text(production_days)}; die externe "
                    f"Beschaffung benötigt {duration_text(procurement_days)}. Daher wird die "
                    "schnellere interne Produktion gewählt."
                )
        elif chosen["method"] == "production":
            reason = (
                "Die vollständige Fehlmenge kann intern produziert werden; eine "
                "vollständige externe Beschaffung ist nicht verfügbar."
            )
        else:
            reason = (
                "Die vollständige Fehlmenge kann extern beschafft werden; eine "
                "vollständige interne Produktion ist nicht verfügbar."
            )

        return {
            "possible": True,
            **chosen,
            "reason": reason,
            "evaluated_routes": candidates,
        }

    return {
        "possible": False,
        "method": "manual",
        "duration_days": None,
        "reason": (
            "Weder Lagerbestand noch interne Produktion oder externe Beschaffung "
            "decken die vollständige Auftragsmenge ab."
        ),
        "evaluated_routes": [],
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

            # Produktion und Lieferant werden immer unabhängig geprüft. Nur so kann
            # der Orchestrator den schnellsten vollständigen Weg auswählen.
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
        delivery["evaluated_routes"] = fulfillment["evaluated_routes"]

    return {
        "customer": customer,
        "stock": stock,
        "capacity": capacity,
        "procurement": procurement,
        "price": price,
        "delivery": delivery,
    }

