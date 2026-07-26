"""Hermes remote-control host protocol primitives."""

from remote_control.authorization import (
    authorize_remote_action,
    unknown_message_disposition,
)
from remote_control.models import ValidationIssue, ValidationResult
from remote_control.protocol import (
    REMOTE_CONTROL_PROTOCOL,
    canonicalize_remote_document,
    remote_document_hash,
    validate_remote_control_document,
    verify_signed_document,
)

__all__ = [
    "REMOTE_CONTROL_PROTOCOL",
    "ValidationIssue",
    "ValidationResult",
    "authorize_remote_action",
    "canonicalize_remote_document",
    "remote_document_hash",
    "unknown_message_disposition",
    "validate_remote_control_document",
    "verify_signed_document",
]
