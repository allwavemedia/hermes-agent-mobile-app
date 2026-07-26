"""Validation for the versioned Hermes remote-control protocol."""

import base64
import hashlib
import hmac
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Iterable, TypeAlias, cast

import jwt
import rfc8785
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from jsonschema.protocols import Validator

from remote_control.models import ValidationIssue, ValidationResult


REMOTE_CONTROL_PROTOCOL: Final = "hermes.remote-control/1.0"
_JWS_TYPE: Final = "hermes-remote-control+jws"
JsonValue: TypeAlias = (
    bool
    | int
    | str
    | float
    | None
    | Sequence["JsonValue"]
    | Mapping[str, "JsonValue"]
)
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


def _without_signature(value: JsonValue) -> JsonValue:
    if not isinstance(value, Mapping):
        return value
    mapping = cast(Mapping[str, JsonValue], value)
    return {key: item for key, item in mapping.items() if key != "signature"}


def canonicalize_remote_document(value: JsonValue) -> bytes:
    """Return RFC 8785 bytes, excluding only the detached signature field."""

    return rfc8785.dumps(_without_signature(value))


def remote_document_hash(value: JsonValue) -> str:
    """Return the protocol's base64url SHA-256 identifier."""

    digest = hashlib.sha256(canonicalize_remote_document(value)).digest()
    encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return f"sha256-{encoded}"


def _decode_segment(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def verify_signed_document(
    *,
    document: Mapping[str, Any],
    signature: str,
    public_jwk: Mapping[str, Any],
    now: str,
    expected: Mapping[str, str],
) -> dict[str, bool | str]:
    """Verify canonical ES256 bytes, target binding, and validity window."""

    segments = signature.split(".")
    if len(segments) != 3 or not all(segments):
        return {"valid": False, "reason": "invalid-signature"}

    try:
        header = json.loads(_decode_segment(segments[0]))
    except (ValueError, json.JSONDecodeError):
        return {"valid": False, "reason": "invalid-signature"}

    if not isinstance(header, dict):
        return {"valid": False, "reason": "invalid-signature"}
    if header.get("alg") != "ES256":
        return {"valid": False, "reason": "wrong-algorithm"}
    if header.get("typ") != _JWS_TYPE:
        return {"valid": False, "reason": "invalid-signature"}
    if (
        public_jwk.get("kty") != "EC"
        or public_jwk.get("crv") != "P-256"
        or not isinstance(public_jwk.get("x"), str)
        or not isinstance(public_jwk.get("y"), str)
        or "d" in public_jwk
    ):
        return {"valid": False, "reason": "invalid-signature"}

    try:
        key = jwt.PyJWK.from_dict(dict(public_jwk)).key
        jwt.decode(
            signature,
            key,
            algorithms=["ES256"],
            options={
                "verify_exp": False,
                "verify_iat": False,
                "verify_nbf": False,
            },
        )
        signed_payload = _decode_segment(segments[1])
    except (ValueError, jwt.PyJWTError):
        return {"valid": False, "reason": "invalid-signature"}

    try:
        expected_payload = canonicalize_remote_document(document)
    except (rfc8785.CanonicalizationError, rfc8785.FloatDomainError):
        return {"valid": False, "reason": "payload-mismatch"}
    if not hmac.compare_digest(signed_payload, expected_payload):
        return {"valid": False, "reason": "payload-mismatch"}

    for target in ("computerId", "deviceId", "sessionId"):
        if document.get(target) != expected.get(target):
            return {"valid": False, "reason": "target-mismatch"}

    issued_at = _parse_timestamp(document.get("issuedAt"))
    expires_at = _parse_timestamp(document.get("expiresAt"))
    current_time = _parse_timestamp(now)
    if (
        issued_at is None
        or expires_at is None
        or current_time is None
        or expires_at <= issued_at
    ):
        return {"valid": False, "reason": "invalid-signature"}
    if current_time < issued_at:
        return {"valid": False, "reason": "issued-in-future"}
    if current_time >= expires_at:
        return {"valid": False, "reason": "expired"}

    return {"valid": True}


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
