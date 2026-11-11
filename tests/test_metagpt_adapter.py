import json
from dataclasses import dataclass

from orderflow.metagpt_agents import friendly_metagpt_error
from orderflow.metagpt_worker import (
    build_order_context,
    build_planning_context,
    build_validation_context,
    context_text,
)


@dataclass
class Message:
    content: str


def test_context_text_accepts_metagpt_message_history() -> None:
    history = [Message("Auftrag A"), Message("Planung B")]

    assert context_text(history) == "Auftrag A\n\nPlanung B"


def test_context_text_keeps_plain_text() -> None:
    assert context_text("Auftrag A") == "Auftrag A"


def test_agent_context_is_chained_within_one_order() -> None:
    payload = {"decision": "Externe Beschaffung", "delivery": {"duration_days": 1}}

    order_context = json.loads(build_order_context(payload))
    planning_context = json.loads(build_planning_context(payload, "Annas Auftragssicht"))
    validation_context = json.loads(
        build_validation_context(payload, "Annas Auftragssicht", "Pauls Planungssicht")
    )

    assert order_context["kontrollierte_fakten"] == payload
    assert planning_context["kontrollierte_fakten"] == payload
    assert planning_context["vorheriger_beitrag"]["text"] == "Annas Auftragssicht"
    assert validation_context["kontrollierte_fakten"] == payload
    assert validation_context["vorherige_beiträge"] == [
        {"rolle": "Anna – Auftrags-Agentin", "text": "Annas Auftragssicht"},
        {"rolle": "Paul – Planungs-Agent", "text": "Pauls Planungssicht"},
    ]


def test_context_builders_do_not_keep_state_between_orders() -> None:
    first = json.loads(build_order_context({"order": "A"}))
    second = json.loads(build_order_context({"order": "B"}))

    assert first["kontrollierte_fakten"] == {"order": "A"}
    assert second["kontrollierte_fakten"] == {"order": "B"}
    assert '"order": "A"' not in json.dumps(second)


def test_invalidated_api_key_gets_clear_instructions() -> None:
    error = friendly_metagpt_error(
        "openai.AuthenticationError: Error code: 401 - token_invalidated"
    )

    assert "API-Schlüssel" in error
    assert "--replace-api-key" in error
    assert "Traceback" not in error


def test_error_message_masks_api_keys() -> None:
    error = friendly_metagpt_error("Provider failed with sk-secretkey123456789")

    assert "sk-secretkey123456789" not in error
    assert "[API-Schlüssel ausgeblendet]" in error
