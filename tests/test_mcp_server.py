from mcp import Client

from orderflow.mcp_server import mcp


async def test_mcp_tools_return_structured_results() -> None:
    async with Client(mcp) as client:
        customer = await client.call_tool("get_customer", {"customer_id": "C100"})
        stock = await client.call_tool(
            "check_stock", {"product_id": "P100", "quantity": 10}
        )
        price = await client.call_tool(
            "calculate_price", {"product_id": "P100", "quantity": 10}
        )

    assert customer.structured_content["credit_status"] == "freigegeben"
    assert stock.structured_content["available"] is True
    assert price.structured_content["total_price"] == 4500.0


async def test_mcp_reports_missing_stock() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_stock", {"product_id": "P100", "quantity": 30}
        )

    assert result.structured_content["available"] is False
    assert result.structured_content["missing_quantity"] == 5


async def test_mcp_checks_external_procurement() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_procurement", {"product_id": "P100", "quantity": 50}
        )

    assert result.structured_content["possible"] is True
    assert result.structured_content["lead_time_days"] == 10


async def test_mcp_calculates_production_duration_transparently() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_capacity", {"product_id": "P300", "quantity": 20}
        )

    content = result.structured_content
    assert content["possible"] is True
    assert content["daily_capacity"] == 30.0
    assert content["setup_days"] == 2
    assert content["processing_days"] == 1
    assert content["production_days"] == 3
    assert content["within_week_capacity"] is True
    assert "20 Stück ÷ 30,00" in content["calculation"]


async def test_delivery_date_skips_weekend() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "calculate_delivery_date",
            {
                "requested_date": "2026-11-13",
                "planning_date": "2026-11-13",
                "stock_available": False,
                "production_days": 2,
            },
        )

    assert result.structured_content["promised_date"] == "2026-11-17"
    assert result.structured_content["requested_date_met"] is False


async def test_capacity_can_span_multiple_weeks() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_capacity", {"product_id": "P100", "quantity": 100}
        )

    content = result.structured_content
    assert content["possible"] is True
    assert content["within_week_capacity"] is False
    assert content["production_days"] > 5


async def test_delivery_has_no_false_date_without_fulfillment_route() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "calculate_delivery_date",
            {
                "requested_date": "2026-11-12",
                "planning_date": "2026-11-10",
                "stock_available": False,
                "production_days": 0,
                "fulfillment_possible": False,
                "fulfillment_method": "manual",
            },
        )

    content = result.structured_content
    assert content["promised_date"] is None
    assert content["requested_date_met"] is False
    assert content["duration_days"] is None


async def test_twelve_workdays_from_tenth_november_end_on_twenty_sixth() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "calculate_delivery_date",
            {
                "requested_date": "2026-11-12",
                "planning_date": "2026-11-10",
                "stock_available": False,
                "production_days": 12,
                "fulfillment_possible": True,
                "fulfillment_method": "production",
            },
        )

    content = result.structured_content
    assert content["promised_date"] == "2026-11-26"
    assert content["requested_date_met"] is False

