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


def build_order_context(payload: dict[str, Any]) -> str:
    """Erzeugt Annas auftragsspezifischen, kontrollierten Arbeitskontext."""
    return json.dumps(
        {
            "kontext_typ": "Auftragseingang",
            "kontrollierte_fakten": payload,
            "arbeitsauftrag": (
                "Beschreibe Kundenwunsch und geschäftliche Folge, aber keine Detailrechnung."
            ),
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def build_planning_context(payload: dict[str, Any], order_text: str) -> str:
    """Gibt Paul die Fakten und Annas vorherigen Beitrag als gemeinsamen Kontext."""
    return json.dumps(
        {
            "kontext_typ": "Planung nach Auftragseingang",
            "kontrollierte_fakten": payload,
            "vorheriger_beitrag": {
                "rolle": "Anna – Auftrags-Agentin",
                "text": order_text,
            },
            "arbeitsauftrag": (
                "Baue auf Annas Beitrag auf, ohne ihn zu wiederholen. Vergleiche die technisch "
                "möglichen Erfüllungswege und erkläre die Auswahl."
            ),
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def build_validation_context(
    payload: dict[str, Any], order_text: str, planning_text: str
) -> str:
    """Gibt Vera Fakten und beide vorherigen Agentenbeiträge zur Gegenprüfung."""
    return json.dumps(
        {
            "kontext_typ": "Unabhängige Abschlussprüfung",
            "kontrollierte_fakten": payload,
            "vorherige_beiträge": [
                {"rolle": "Anna – Auftrags-Agentin", "text": order_text},
                {"rolle": "Paul – Planungs-Agent", "text": planning_text},
            ],
            "arbeitsauftrag": (
                "Prüfe die regelbasierte Entscheidung und beide Aussagen gegen die Fakten. "
                "Benenne einen Widerspruch konkret oder bestätige, dass keiner vorliegt."
            ),
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    )


async def review(payload: dict[str, Any]) -> dict[str, str]:
    """Führt die drei echten MetaGPT-Rollen innerhalb der isolierten Laufzeit aus."""
    from metagpt.actions import Action
    from metagpt.roles import Role

    class InterpretOrder(Action):
        name: str = "InterpretOrder"

        async def run(self, context: Any) -> str:
            return await self._aask(
                "Du bist Anna, die Auftrags-Agentin eines Industrieunternehmens. Deine eigene "
                "Perspektive ist der kaufmännische Auftragseingang, nicht die technische Planung. "
                "Beginne mit 'Auftragssicht:'. Erkläre in drei bis vier kurzen deutschen Sätzen "
                "den Kundenwunsch, den Bonitätsstatus, den Wunschtermin und die daraus folgende "
                "fachliche Entscheidung. Erkläre keine Kapazitäts- oder Preisformel und verwende "
                "keine Ich-Vorstellung. Nutze ausschließlich die kontrollierten Fakten, übersetze "
                "technische Statuswerte ins Deutsche und erfinde nichts.\n\n"
                + context_text(context)
            )

    class ExplainPlanning(Action):
        name: str = "ExplainPlanning"

        async def run(self, context: Any) -> str:
            return await self._aask(
                "Du bist Paul, der Planungs-Agent. Du erhältst die kontrollierten MCP-Fakten und "
                "Annas vorherigen Beitrag. Beginne mit 'Planungssicht:' und baue auf Anna auf, "
                "ohne ihre Auftragszusammenfassung zu wiederholen. Vergleiche Lager, interne "
                "Produktion und externe Beschaffung, soweit dazu Daten vorhanden sind. Nenne die "
                "Dauer aller vollständig möglichen Wege, den ausgewählten Weg und den sachlichen "
                "Grund für seine Auswahl. Erkläre danach Preis und Rabatt sowie Wunsch- und "
                "Zusagetermin. Ein Termin ist nur bei 'requested_date_met: true' eingehalten. "
                "Schließe mit genau einem Satz zur Aufgabe von MCP. Verwende sechs bis neun kurze "
                "Sätze, keine Ich-Vorstellung, keine erfundenen Werte und keine neue Entscheidung."
                "\n\n" + context_text(context)
            )

    class ValidateDecision(Action):
        name: str = "ValidateDecision"

        async def run(self, context: Any) -> str:
            return await self._aask(
                "Du bist Vera, die unabhängige Validierungs-Agentin. Du erhältst die "
                "kontrollierten Fakten sowie Annas und Pauls vorherige Beiträge. Schreibe keine "
                "dritte Auftragszusammenfassung. Beginne exakt mit 'Prüfergebnis: plausibel.' oder "
                "'Prüfergebnis: nicht plausibel.'. Prüfe danach in vier kurzen, getrennten "
                "Zeilen: 'Bonität:', 'Menge und Erfüllungsweg:', 'Preis:' und 'Termin:'. Gleiche "
                "dabei auch die Aussagen der beiden Agenten mit den Fakten ab. Ein Termin gilt nur "
                "bei 'requested_date_met: true' als eingehalten. Nenne anschließend konkret, ob "
                "ein Widerspruch gefunden wurde, und schließe mit dem nächsten Prozessschritt. "
                "Verändere die regelbasierte Entscheidung nicht, erfinde keine Werte und verwende "
                "leicht verständliches Deutsch.\n\n" + context_text(context)
            )

    class OrderAgent(Role):
        name: str = "Anna"
        profile: str = "Auftrags-Agent"
        goal: str = "Kundenwunsch und kaufmännische Prozessfolge knapp einordnen"
        constraints: str = "Keine Planung berechnen und keine Werte ergänzen oder verändern"

        def __init__(self, **kwargs: Any):
            super().__init__(**kwargs)
            self.set_actions([InterpretOrder])

    class PlanningAgent(Role):
        name: str = "Paul"
        profile: str = "Planungs-Agent"
        goal: str = "Mögliche Erfüllungswege vergleichen und die Auswahl erklären"
        constraints: str = "Auf Anna aufbauen und nur bereitgestellte Fakten verwenden"

        def __init__(self, **kwargs: Any):
            super().__init__(**kwargs)
            self.set_actions([ExplainPlanning])

    class ValidationAgent(Role):
        name: str = "Vera"
        profile: str = "Validierungs-Agent"
        goal: str = "Fakten, Entscheidung und beide Agentenbeiträge gegeneinander prüfen"
        constraints: str = "Keine Zusammenfassung wiederholen und Entscheidung nicht verändern"

        def __init__(self, **kwargs: Any):
            super().__init__(**kwargs)
            self.set_actions([ValidateDecision])

    order_message = await OrderAgent().run(build_order_context(payload))
    order_text = getattr(order_message, "content", str(order_message))

    planning_message = await PlanningAgent().run(build_planning_context(payload, order_text))
    planning_text = getattr(planning_message, "content", str(planning_message))

    validation_context = build_validation_context(payload, order_text, planning_text)
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
