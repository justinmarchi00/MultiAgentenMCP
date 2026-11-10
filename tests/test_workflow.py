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


async def test_capacity_shortage_triggers_procurement() -> None:
    result = await run_order_workflow(order("C100", "P100", 80))

    assert result.decision is WorkflowDecision.PROCUREMENT_REQUIRED
    assert result.capacity["possible"] is True
    assert result.capacity["within_week_capacity"] is False
    assert result.procurement["possible"] is True
    assert result.delivery["fulfillment_method"] == "procurement"


async def test_blocked_customer_requires_manual_review() -> None:
    result = await run_order_workflow(order("C200", "P100", 10))

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


def test_fulfillment_never_uses_incomplete_supplier_route() -> None:
    route = _select_fulfillment(
        {"available": False},
        {"possible": False, "within_week_capacity": False},
        {"possible": False, "lead_time_days": 1},
    )

    assert route["possible"] is False
    assert route["method"] == "manual"
    assert route["duration_days"] is None

