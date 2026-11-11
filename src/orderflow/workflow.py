from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from datetime import date
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

DECISION_LABELS = {
    WorkflowDecision.CONFIRMED: "Auftrag bestätigen",
    WorkflowDecision.PRODUCTION_REQUIRED: "Interne Produktion erforderlich",
    WorkflowDecision.PROCUREMENT_REQUIRED: "Externe Beschaffung erforderlich",
    WorkflowDecision.MANUAL_REVIEW: "Manuelle Prüfung erforderlich",
}


def _format_money(value: Any, currency: str = "EUR") -> str:
    try:
        amount = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "nicht ermittelbar"
    return f"{amount} {currency}"


def _format_date(value: Any) -> str:
    try:
        return date.fromisoformat(str(value)).strftime("%d.%m.%Y")
    except ValueError:
        return "nicht ermittelbar"


def _format_duration(value: Any) -> str:
    try:
        duration = int(value)
    except (TypeError, ValueError):
        return "nicht ermittelbar"
    unit = "Arbeitstag" if duration == 1 else "Arbeitstage"
    return f"{duration} {unit}"


def _determine_decision(facts: dict[str, Any]) -> tuple[WorkflowDecision, str]:
    customer = facts["customer"]
    stock = facts["stock"]
    price = facts["price"]
    delivery = facts["delivery"]

    if not customer.get("found"):
        return WorkflowDecision.MANUAL_REVIEW, "Kunde wurde nicht gefunden."
    if customer.get("credit_status") != "freigegeben":
        return WorkflowDecision.MANUAL_REVIEW, "Bonitätsstatus ist nicht freigegeben."
    if "error" in stock or "error" in price:
        return WorkflowDecision.MANUAL_REVIEW, "Produkt- oder Preisdaten sind unvollständig."
    fulfillment_method = delivery.get("fulfillment_method")
    requested_date_met = bool(delivery.get("requested_date_met"))
    if stock.get("available") and fulfillment_method == "stock" and requested_date_met:
        return WorkflowDecision.CONFIRMED, "Bonität und Lagerbestand sind ausreichend."
    if stock.get("available") and fulfillment_method == "stock":
        return (
            WorkflowDecision.MANUAL_REVIEW,
            "Die Ware ist verfügbar, der angefragte Liefertermin liegt jedoch vor dem "
            "frühestmöglichen Zusagetermin.",
        )
    if fulfillment_method == "production":
        duration = delivery.get("duration_days", 0)
        schedule_note = (
            "Der Wunschtermin kann eingehalten werden."
            if requested_date_met
            else "Der Wunschtermin kann nicht eingehalten werden."
        )
        return (
            WorkflowDecision.PRODUCTION_REQUIRED,
            f"{delivery.get('fulfillment_reason', 'Die Fehlmenge wird intern produziert.')} "
            f"Gewählte Durchlaufzeit: {_format_duration(duration)}. {schedule_note}",
        )
    if fulfillment_method == "procurement":
        schedule_note = (
            "Der Wunschtermin kann eingehalten werden."
            if requested_date_met
            else "Der Wunschtermin kann nicht eingehalten werden."
        )
        return (
            WorkflowDecision.PROCUREMENT_REQUIRED,
            f"{delivery.get('fulfillment_reason', 'Die Fehlmenge wird extern beschafft.')} "
            f"{schedule_note}",
        )
    return (
        WorkflowDecision.MANUAL_REVIEW,
        "Kein vollständiger Erfüllungsweg ist automatisch planbar; Termin und Menge "
        "müssen manuell geprüft werden.",
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
        "Prozess-Orchestrator",
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
        "MCP: Kundendaten abrufen",
        f"Kundenstatus: {customer.get('credit_status', customer.get('error', 'unbekannt'))}.",
        level=EventLevel.SUCCESS if customer.get("found") else EventLevel.WARNING,
        details=customer,
    )
    stock = facts["stock"]
    await emit(
        3,
        "Planungs-Agent",
        "MCP: Lagerbestand prüfen",
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
            "MCP: Produktionskapazität berechnen",
            (
                f"Die Fehlmenge kann produziert werden: {capacity.get('calculation', '')}."
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
            "MCP: Beschaffung prüfen",
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
        "MCP: Preis berechnen",
        (
            f"Gesamtpreis: {_format_money(price.get('total_price'), price.get('currency', 'EUR'))}."
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
        "MCP: Liefertermin berechnen",
        (
            f"Zugesagter Liefertermin: {_format_date(delivery.get('promised_date'))}."
            if delivery.get("promised_date")
            else "Kein belastbarer Liefertermin automatisch ermittelbar."
        ),
        level=(
            EventLevel.SUCCESS
            if delivery.get("fulfillment_possible") and "error" not in delivery
            else EventLevel.WARNING
        ),
        details=delivery,
    )

    decision, explanation = _determine_decision(facts)
    result_payload = {
        "order": order.model_dump(mode="json"),
        "decision": DECISION_LABELS[decision],
        "explanation": explanation,
        **facts,
    }

    metagpt_summary = None
    metagpt_used = False
    metagpt_messages: dict[str, str] = {}
    if use_metagpt:
        await emit(
            4,
            "MetaGPT-Team",
            "Agentenreview starten",
            "Anna ordnet den Auftrag ein, Paul baut darauf auf und Vera prüft beide Beiträge.",
        )
        try:
            from orderflow.metagpt_agents import run_metagpt_review

            review = await run_metagpt_review(result_payload)
            metagpt_summary = review["validation_agent"]
            metagpt_messages = review
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
        metagpt_messages=metagpt_messages,
    )

