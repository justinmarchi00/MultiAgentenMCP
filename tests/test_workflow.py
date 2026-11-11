from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from orderflow.mcp_client import _select_fulfillment
from orderflow.models import OrderRequest, WorkflowDecision
from orderflow.workflow import run_order_workflow


def order(customer: str, product: str, quantity: int) -> OrderRequest:
    return OrderRequest(
        customer_id=customer,
        product_id=product,
        quantity=quantity,
        requested_date=date.today() + timedelta(days=14),
    )


async def test_normal_order_is_confirmed() -> None:
    result = await run_order_workflow(order("C100", "P100", 10))

    assert result.decision is WorkflowDecision.CONFIRMED
    assert result.stock["available"] is True
    assert result.price["total_price"] == 4500.0
    assert len(result.events) >= 6


async def test_missing_stock_triggers_production() -> None:
    result = await run_order_workflow(order("C100", "P100", 30))

    assert result.decision is WorkflowDecision.PRODUCTION_REQUIRED
    assert result.stock["missing_quantity"] == 5
    assert result.capacity["possible"] is True


async def test_faster_supplier_is_selected_even_when_weekly_capacity_is_enough() -> None:
    result = await run_order_workflow(order("C100", "P500", 120))

    assert result.decision is WorkflowDecision.PROCUREMENT_REQUIRED
    assert result.capacity["possible"] is True
    assert result.capacity["within_week_capacity"] is True
    assert result.capacity["production_days"] == 3
    assert result.procurement["possible"] is True
    assert result.procurement["lead_time_days"] == 1
    assert result.delivery["fulfillment_method"] == "procurement"
    assert result.delivery["duration_days"] == 1
    assert "schneller" in result.explanation


async def test_faster_internal_production_is_selected() -> None:
    result = await run_order_workflow(order("C100", "P100", 30))

    assert result.decision is WorkflowDecision.PRODUCTION_REQUIRED
    assert result.capacity["production_days"] == 2
    assert result.procurement["possible"] is True
    assert result.procurement["lead_time_days"] == 10
    assert result.delivery["fulfillment_method"] == "production"


async def test_multiweek_production_is_selected_if_supplier_cannot_cover_all() -> None:
    result = await run_order_workflow(order("C100", "P100", 200))

    assert result.stock["missing_quantity"] == 175
    assert result.capacity["within_week_capacity"] is False
    assert result.capacity["possible"] is True
    assert result.procurement["possible"] is False
    assert result.delivery["fulfillment_method"] == "production"


async def test_no_complete_route_requires_manual_review() -> None:
    result = await run_order_workflow(order("C100", "P400", 100))

    assert result.capacity["possible"] is False
    assert result.procurement["possible"] is False
    assert result.delivery["fulfillment_possible"] is False
    assert result.delivery["promised_date"] is None
    assert result.decision is WorkflowDecision.MANUAL_REVIEW


async def test_blocked_customer_requires_manual_review() -> None:
    result = await run_order_workflow(order("C200", "P100", 10))

    assert result.decision is WorkflowDecision.MANUAL_REVIEW
    assert "Bonitätsstatus" in result.explanation


async def test_customer_under_review_requires_manual_review() -> None:
    result = await run_order_workflow(order("C300", "P100", 10))

    assert result.decision is WorkflowDecision.MANUAL_REVIEW
    assert "Bonitätsstatus" in result.explanation


async def test_unknown_product_requires_manual_review() -> None:
    result = await run_order_workflow(order("C100", "UNKNOWN", 10))

    assert result.decision is WorkflowDecision.MANUAL_REVIEW
    assert "error" in result.stock


def test_quantity_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        order("C100", "P100", 0)


def test_fulfillment_falls_back_to_multiweek_production() -> None:
    route = _select_fulfillment(
        {"available": False},
        {
            "possible": True,
            "within_week_capacity": False,
            "production_days": 12,
        },
        {"possible": False, "lead_time_days": 1},
    )

    assert route["possible"] is True
    assert route["method"] == "production"
    assert route["duration_days"] == 12


def test_fulfillment_selects_faster_complete_procurement() -> None:
    route = _select_fulfillment(
        {"available": False},
        {"possible": True, "within_week_capacity": True, "production_days": 3},
        {"possible": True, "lead_time_days": 1},
    )

    assert route["method"] == "procurement"
    assert route["duration_days"] == 1
    assert len(route["evaluated_routes"]) == 2


def test_fulfillment_selects_faster_complete_production() -> None:
    route = _select_fulfillment(
        {"available": False},
        {"possible": True, "within_week_capacity": True, "production_days": 2},
        {"possible": True, "lead_time_days": 6},
    )

    assert route["method"] == "production"
    assert route["duration_days"] == 2


def test_fulfillment_prefers_internal_production_on_equal_duration() -> None:
    route = _select_fulfillment(
        {"available": False},
        {"possible": True, "within_week_capacity": True, "production_days": 3},
        {"possible": True, "lead_time_days": 3},
    )

    assert route["method"] == "production"
    assert "Gleichstand" in route["reason"]


def test_fulfillment_uses_supplier_at_exact_quantity_limit() -> None:
    route = _select_fulfillment(
        {"available": False},
        {"possible": False, "production_days": 0},
        {"possible": True, "required_quantity": 100, "maximum_quantity": 100, "lead_time_days": 1},
    )

    assert route["method"] == "procurement"
    assert route["duration_days"] == 1


def test_fulfillment_never_uses_incomplete_supplier_route() -> None:
    route = _select_fulfillment(
        {"available": False},
        {"possible": False, "within_week_capacity": False},
        {"possible": False, "lead_time_days": 1},
    )

    assert route["possible"] is False
    assert route["method"] == "manual"
    assert route["duration_days"] is None

