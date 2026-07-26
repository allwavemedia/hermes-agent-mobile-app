"""Validation for the versioned Hermes remote-control protocol."""

import json
from pathlib import Path
from typing import Final, Iterable

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from jsonschema.protocols import Validator

from remote_control.models import ValidationIssue, ValidationResult


REMOTE_CONTROL_PROTOCOL: Final = "hermes.remote-control/1.0"
_SCHEMA_NAMES: Final = frozenset(
    {"capability", "command", "envelope", "event", "pairing", "snapshot"}
)
_SCHEMA_ROOT: Final = (
    Path(__file__).resolve().parents[1] / "docs" / "remote-control" / "schemas" / "v1"
)


def _load_validators() -> dict[str, Validator]:
    validators: dict[str, Validator] = {}
    for schema_name in sorted(_SCHEMA_NAMES):
        schema_path = _SCHEMA_ROOT / f"{schema_name}.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validators[schema_name] = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )
    return validators


_VALIDATORS: Final = _load_validators()


def _json_pointer(parts: Iterable[object]) -> str:
    return "".join(
        f"/{str(part).replace('~', '~0').replace('/', '~1')}" for part in parts
    )


def _to_validation_issue(error: ValidationError) -> ValidationIssue:
    return ValidationIssue(
        instance_path=_json_pointer(error.absolute_path),
        keyword=str(error.validator),
        message=error.message,
        schema_path=_json_pointer(error.absolute_schema_path),
    )


def validate_remote_control_document(
    schema_name: str,
    value: object,
) -> ValidationResult:
    """Validate an untrusted document without applying protocol authority."""

    validator = _VALIDATORS.get(schema_name)
    if validator is None:
        return ValidationResult(
            valid=False,
            errors=(
                ValidationIssue(
                    instance_path="",
                    keyword="schema",
                    message=f"unknown remote-control schema: {schema_name}",
                    schema_path="",
                ),
            ),
        )

    errors = tuple(
        _to_validation_issue(error)
        for error in sorted(
            validator.iter_errors(value),
            key=lambda candidate: (
                tuple(str(part) for part in candidate.absolute_path),
                tuple(str(part) for part in candidate.absolute_schema_path),
                candidate.message,
            ),
        )
    )
    return ValidationResult(valid=not errors, errors=errors)
