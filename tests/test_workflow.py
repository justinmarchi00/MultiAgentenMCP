from datetime import date, timedelta

import pytest
from pydantic import ValidationError

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
    assert result.capacity["possible"] is False
    assert result.procurement["possible"] is True


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

