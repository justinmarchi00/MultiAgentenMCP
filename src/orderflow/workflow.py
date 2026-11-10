from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from time import perf_counter
from typing import Any

from orderflow.mcp_client import evaluate_order_via_mcp
from orderflow.models import (
    EventLevel,
    OrderRequest,
    WorkflowDecision,
    WorkflowEvent,
    WorkflowResult,
)

EventCallback = Callable[[WorkflowEvent], None]


def _determine_decision(facts: dict[str, Any]) -> tuple[WorkflowDecision, str]:
    customer = facts["customer"]
    stock = facts["stock"]
    capacity = facts["capacity"]
    procurement = facts["procurement"]
    price = facts["price"]

    if not customer.get("found"):
        return WorkflowDecision.MANUAL_REVIEW, "Kunde wurde nicht gefunden."
    if customer.get("credit_status") != "freigegeben":
        return WorkflowDecision.MANUAL_REVIEW, "Bonitätsstatus ist nicht freigegeben."
    if "error" in stock or "error" in price:
        return WorkflowDecision.MANUAL_REVIEW, "Produkt- oder Preisdaten sind unvollständig."
    if stock.get("available"):
        return WorkflowDecision.CONFIRMED, "Bonität und Lagerbestand sind ausreichend."
    if capacity and capacity.get("possible"):
        return (
            WorkflowDecision.PRODUCTION_REQUIRED,
            "Der Lagerbestand reicht nicht aus, die Fehlmenge kann jedoch produziert werden.",
        )
    if procurement and procurement.get("possible"):
        return (
            WorkflowDecision.PROCUREMENT_REQUIRED,
            "Der Bestand und die interne Kapazität reichen nicht aus; "
            "die Fehlmenge kann extern beschafft werden.",
        )
    return (
        WorkflowDecision.MANUAL_REVIEW,
        "Weder Lagerbestand noch verfügbare Produktionskapazität reichen aus.",
    )


async def run_order_workflow(
    order: OrderRequest,
    *,
    use_metagpt: bool = False,
    event_callback: EventCallback | None = None,
    demo_delay_seconds: float | None = None,
) -> WorkflowResult:
    started = perf_counter()
    events: list[WorkflowEvent] = []
    delay = (
        float(os.getenv("ORDERFLOW_DEMO_DELAY_SECONDS", "0"))
        if demo_delay_seconds is None
        else demo_delay_seconds
    )

    async def emit(
        step: int,
        agent: str,
        action: str,
        message: str,
        *,
        level: EventLevel = EventLevel.INFO,
        details: dict[str, Any] | None = None,
    ) -> None:
        event = WorkflowEvent(
            step=step,
            agent=agent,
            action=action,
            message=message,
            level=level,
            details=details or {},
        )
        events.append(event)
        if event_callback:
            event_callback(event)
        if delay > 0:
            await asyncio.sleep(delay)

    await emit(
        1,
        "Workflow-Orchestrator",
        "Auftrag annehmen",
        f"Auftrag {order.customer_id}/{order.product_id}/{order.quantity} wurde angenommen.",
    )
    await emit(
        2,
        "Auftrags-Agent",
        "Pflichtdaten prüfen",
        "Alle Pflichtdaten sind vorhanden und formal gültig.",
        level=EventLevel.SUCCESS,
    )
    await emit(
        3,
        "Planungs-Agent",
        "MCP-Werkzeuge aufrufen",
        "Kunden-, Bestands-, Kapazitäts-, Preis- und Lieferdaten werden abgefragt.",
    )

    facts = await evaluate_order_via_mcp(order)

    customer = facts["customer"]
    await emit(
        3,
        "Planungs-Agent",
        "MCP: get_customer",
        f"Kundenstatus: {customer.get('credit_status', customer.get('error', 'unbekannt'))}.",
        level=EventLevel.SUCCESS if customer.get("found") else EventLevel.WARNING,
        details=customer,
    )
    stock = facts["stock"]
    await emit(
        3,
        "Planungs-Agent",
        "MCP: check_stock",
        (
            f"Bestand ausreichend: {stock.get('current_stock', 0)} Stück verfügbar."
            if stock.get("available")
            else f"Fehlmenge: {stock.get('missing_quantity', 0)} Stück."
        ),
        level=EventLevel.SUCCESS if stock.get("available") else EventLevel.WARNING,
        details=stock,
    )
    if facts["capacity"] is not None:
        capacity = facts["capacity"]
        await emit(
            3,
            "Planungs-Agent",
            "MCP: check_capacity",
            (
                "Die Fehlmenge kann produziert werden."
                if capacity.get("possible")
                else "Die Fehlmenge übersteigt die verfügbare Wochenkapazität."
            ),
            level=EventLevel.SUCCESS if capacity.get("possible") else EventLevel.WARNING,
            details=capacity,
        )
    if facts["procurement"] is not None:
        procurement = facts["procurement"]
        await emit(
            3,
            "Beschaffungs-Agent",
            "MCP: check_procurement",
            (
                f"Externe Beschaffung bei {procurement.get('supplier')} ist möglich."
                if procurement.get("possible")
                else "Für die Fehlmenge ist keine ausreichende Beschaffungsoption vorhanden."
            ),
            level=(
                EventLevel.SUCCESS if procurement.get("possible") else EventLevel.WARNING
            ),
            details=procurement,
        )
    price = facts["price"]
    await emit(
        3,
        "Kalkulations-Agent",
        "MCP: calculate_price",
        (
            f"Gesamtpreis: {price.get('total_price')} {price.get('currency', 'EUR')}."
            if "error" not in price
            else price["error"]
        ),
        level=EventLevel.SUCCESS if "error" not in price else EventLevel.WARNING,
        details=price,
    )
    delivery = facts["delivery"]
    await emit(
        3,
        "Planungs-Agent",
        "MCP: calculate_delivery_date",
        f"Zugesagter Liefertermin: {delivery.get('promised_date', 'nicht ermittelbar')}.",
        level=EventLevel.SUCCESS if "error" not in delivery else EventLevel.WARNING,
        details=delivery,
    )

    decision, explanation = _determine_decision(facts)
    result_payload = {
        "order": order.model_dump(mode="json"),
        "decision": decision.value,
        "explanation": explanation,
        **facts,
    }

    metagpt_summary = None
    metagpt_used = False
    if use_metagpt:
        await emit(
            4,
            "MetaGPT-Team",
            "Agentenreview starten",
            "Auftrags-, Planungs- und Validierungs-Agent erklären das Ergebnis.",
        )
        try:
            from orderflow.metagpt_agents import run_metagpt_review

            review = await run_metagpt_review(result_payload)
            metagpt_summary = review["validation_agent"]
            metagpt_used = True
            for agent_key, label in (
                ("order_agent", "Auftrags-Agent"),
                ("planning_agent", "Planungs-Agent"),
                ("validation_agent", "Validierungs-Agent"),
            ):
                await emit(
                    4,
                    label,
                    "MetaGPT-Nachricht",
                    review[agent_key],
                    level=EventLevel.SUCCESS,
                )
        except Exception as exc:  # MetaGPT-Konfiguration ist optional.
            metagpt_summary = f"MetaGPT konnte nicht gestartet werden: {exc}"
            await emit(
                4,
                "MetaGPT-Team",
                "Fallback",
                metagpt_summary,
                level=EventLevel.WARNING,
            )

    level = EventLevel.SUCCESS
    if decision is WorkflowDecision.MANUAL_REVIEW:
        level = EventLevel.WARNING
    await emit(
        5,
        "Validierungs-Agent",
        "Entscheidung validieren",
        explanation,
        level=level,
        details={"decision": decision.value},
    )

    return WorkflowResult(
        order=order,
        decision=decision,
        explanation=explanation,
        customer=facts["customer"],
        stock=facts["stock"],
        capacity=facts["capacity"],
        procurement=facts["procurement"],
        price=facts["price"],
        delivery=facts["delivery"],
        events=events,
        processing_seconds=perf_counter() - started,
        metagpt_used=metagpt_used,
        metagpt_summary=metagpt_summary,
    )

