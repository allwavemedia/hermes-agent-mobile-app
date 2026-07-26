"""Hermes remote-control host protocol primitives."""

from remote_control.adapter import GatewaySessionAdapter
from remote_control.authorization import (
    authorize_remote_action,
    unknown_message_disposition,
)
from remote_control.models import (
    AdapterProjectionError,
    AdapterSessionContext,
    CommandReceipt,
    RemoteCommandActor,
    SnapshotRequired,
    UnknownCriticalGatewayEvent,
    ValidationIssue,
    ValidationResult,
)
from remote_control.protocol import (
    REMOTE_CONTROL_PROTOCOL,
    canonicalize_remote_document,
    remote_document_hash,
    validate_remote_control_document,
    verify_signed_document,
)

__all__ = [
    "REMOTE_CONTROL_PROTOCOL",
    "AdapterProjectionError",
    "AdapterSessionContext",
    "CommandReceipt",
    "GatewaySessionAdapter",
    "RemoteCommandActor",
    "SnapshotRequired",
    "UnknownCriticalGatewayEvent",
    "ValidationIssue",
    "ValidationResult",
    "authorize_remote_action",
    "canonicalize_remote_document",
    "remote_document_hash",
    "unknown_message_disposition",
    "validate_remote_control_document",
    "verify_signed_document",
]
