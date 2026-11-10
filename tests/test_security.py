import re
from pathlib import Path


def test_example_configuration_contains_no_real_api_key() -> None:
    example = Path(__file__).resolve().parents[1] / "config" / "config2.example.yaml"
    content = example.read_text(encoding="utf-8")

    assert "sk-demo-not-configured" in content
    assert re.search(r"sk-[A-Za-z0-9_-]{20,}", content) is None
