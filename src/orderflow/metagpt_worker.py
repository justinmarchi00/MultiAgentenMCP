from __future__ import annotations

import asyncio
import json
import sys
from typing import Any


def context_text(context: Any) -> str:
    """Wandelt den von MetaGPT übergebenen Nachrichtenverlauf in Prompt-Text um."""
    if isinstance(context, str):
        return context
    if isinstance(context, list):
        return "\n\n".join(str(getattr(message, "content", message)) for message in context)
    return str(context)


async def review(payload: dict[str, Any]) -> dict[str, str]:
    """Führt die drei echten MetaGPT-Rollen innerhalb der isolierten Laufzeit aus."""
    from metagpt.actions import Action
    from metagpt.roles import Role

    class InterpretOrder(Action):
        name: str = "InterpretOrder"

        async def run(self, context: Any) -> str:
            return await self._aask(
                "Du bist der Auftrags-Agent eines Industrieunternehmens. Fasse den folgenden "
                "strukturierten Auftrag auf Deutsch in höchstens drei sachlichen Sätzen zusammen. "
                "Erfinde keine Daten.\n\n" + context_text(context)
            )

    class ExplainPlanning(Action):
        name: str = "ExplainPlanning"

        async def run(self, context: Any) -> str:
            return await self._aask(
                "Du bist der Planungs-Agent. Erkläre die über MCP ermittelten Fakten zu Bestand, "
                "Kapazität, Beschaffung, Preis und Liefertermin auf Deutsch. Nutze höchstens vier "
                "Sätze und erfinde keine Werte.\n\n" + context_text(context)
            )

    class ValidateDecision(Action):
        name: str = "ValidateDecision"

        async def run(self, context: Any) -> str:
            return await self._aask(
                "Du bist der Validierungs-Agent. Prüfe, ob die bereits regelbasiert getroffene "
                "Entscheidung zu den gelieferten Fakten passt. Formuliere eine kurze, sachliche "
                "Begründung auf Deutsch. Verändere die Entscheidung nicht und erfinde keine Daten."
                "\n\n" + context_text(context)
            )

    class OrderAgent(Role):
        name: str = "Anna"
        profile: str = "Auftrags-Agent"
        goal: str = "Auftragsdaten eindeutig und knapp zusammenfassen"
        constraints: str = "Keine Werte ergänzen oder verändern"

        def __init__(self, **kwargs: Any):
            super().__init__(**kwargs)
            self.set_actions([InterpretOrder])

    class PlanningAgent(Role):
        name: str = "Paul"
        profile: str = "Planungs-Agent"
        goal: str = "MCP-Ergebnisse verständlich erklären"
        constraints: str = "Nur bereitgestellte Fakten verwenden"

        def __init__(self, **kwargs: Any):
            super().__init__(**kwargs)
            self.set_actions([ExplainPlanning])

    class ValidationAgent(Role):
        name: str = "Vera"
        profile: str = "Validierungs-Agent"
        goal: str = "Regelbasierte Entscheidung plausibilisieren"
        constraints: str = "Entscheidung nicht verändern"

        def __init__(self, **kwargs: Any):
            super().__init__(**kwargs)
            self.set_actions([ValidateDecision])

    context = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    order_message = await OrderAgent().run(context)
    planning_message = await PlanningAgent().run(context)
    order_text = getattr(order_message, "content", str(order_message))
    planning_text = getattr(planning_message, "content", str(planning_message))

    validation_context = json.dumps(
        {
            "regelbasiertes_ergebnis": payload,
            "auftrags_agent": order_text,
            "planungs_agent": planning_text,
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    )
    validation_message = await ValidationAgent().run(validation_context)
    return {
        "order_agent": order_text,
        "planning_agent": planning_text,
        "validation_agent": getattr(validation_message, "content", str(validation_message)),
    }


def main() -> None:
    payload = json.loads(sys.stdin.read())
    result = asyncio.run(review(payload))
    print("ORDERFLOW_METAGPT_RESULT=" + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
