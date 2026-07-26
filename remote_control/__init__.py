"""Hermes remote-control host protocol primitives."""

from remote_control.models import ValidationIssue, ValidationResult
from remote_control.protocol import (
    REMOTE_CONTROL_PROTOCOL,
    validate_remote_control_document,
)

__all__ = [
    "REMOTE_CONTROL_PROTOCOL",
    "ValidationIssue",
    "ValidationResult",
    "validate_remote_control_document",
]
