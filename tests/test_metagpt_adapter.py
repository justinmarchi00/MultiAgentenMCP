from dataclasses import dataclass

from orderflow.metagpt_worker import context_text


@dataclass
class Message:
    content: str


def test_context_text_accepts_metagpt_message_history() -> None:
    history = [Message("Auftrag A"), Message("Planung B")]

    assert context_text(history) == "Auftrag A\n\nPlanung B"


def test_context_text_keeps_plain_text() -> None:
    assert context_text("Auftrag A") == "Auftrag A"
