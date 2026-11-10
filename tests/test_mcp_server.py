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

