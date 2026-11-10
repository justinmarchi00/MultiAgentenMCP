from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date, timedelta

from orderflow.models import OrderRequest
from orderflow.workflow import run_order_workflow


def scenario_order(name: str) -> OrderRequest:
    requested = date.today() + timedelta(days=14)
    scenarios = {
        "normal": OrderRequest(
            customer_id="C100", product_id="P100", quantity=10, requested_date=requested
        ),
        "production": OrderRequest(
            customer_id="C100", product_id="P100", quantity=30, requested_date=requested
        ),
        "procurement": OrderRequest(
            customer_id="C100", product_id="P100", quantity=80, requested_date=requested
        ),
        "blocked": OrderRequest(
            customer_id="C200", product_id="P100", quantity=10, requested_date=requested
        ),
    }
    return scenarios[name]


async def _run(args: argparse.Namespace) -> None:
    order = scenario_order(args.scenario)

    def show_event(event: object) -> None:
        print(f"[{event.step}] {event.agent} · {event.action}: {event.message}")

    result = await run_order_workflow(
        order,
        use_metagpt=args.metagpt,
        event_callback=show_event,
    )
    print("\nErgebnis:")
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="OrderFlow BPM-Prototyp")
    parser.add_argument(
        "--scenario",
        choices=["normal", "production", "procurement", "blocked"],
        default="normal",
    )
    parser.add_argument("--metagpt", action="store_true", help="MetaGPT-Review aktivieren")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()

