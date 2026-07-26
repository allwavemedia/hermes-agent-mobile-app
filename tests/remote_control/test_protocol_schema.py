import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = (
    REPOSITORY_ROOT
    / "apps"
    / "remote-control-protocol"
    / "fixtures"
    / "v1"
    / "validation-cases.json"
)
VALIDATION_CASES: list[dict[str, Any]] = json.loads(
    CASES_PATH.read_text(encoding="utf-8")
)


def _load_protocol_module() -> ModuleType | None:
    try:
        return importlib.import_module("remote_control.protocol")
    except ModuleNotFoundError as error:
        if error.name in {"remote_control", "remote_control.protocol"}:
            return None
        raise


@pytest.mark.parametrize(
    ("schema_name", "value", "expected"),
    [
        (test_case["schema"], test_case["value"], test_case["expected"])
        for test_case in VALIDATION_CASES
    ],
    ids=[test_case["name"] for test_case in VALIDATION_CASES],
)
def test_v1_schema_validation_matches_contract(
    schema_name: str,
    value: object,
    expected: bool,
) -> None:
    protocol = _load_protocol_module()

    assert protocol is not None, "the Python protocol validator must exist"
    result = protocol.validate_remote_control_document(schema_name, value)
    assert result.valid is expected
