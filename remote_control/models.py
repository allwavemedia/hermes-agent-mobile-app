"""Framework-neutral remote-control protocol and adapter result models."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One stable, serializable JSON Schema validation issue."""

    instance_path: str
    keyword: str
    message: str
    schema_path: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """The result of validating one untrusted protocol document."""

    valid: bool
    errors: tuple[ValidationIssue, ...]


@dataclass(frozen=True, slots=True)
class AdapterSessionContext:
    """Current authenticated, capability-bound context for one live session."""

    computer_id: str
    session_id: str
    session_revision: int
    capability_hash: str
    active_run_id: str | None
    issued_at: str
    expires_at: str
    signature: str
    reasoning_visible: bool = False


@dataclass(frozen=True, slots=True)
class RemoteCommandActor:
    """Authenticated command bindings presented to the adapter."""

    authenticated_session_id: str
    session_revision: int
    capability_hash: str


@dataclass(frozen=True, slots=True)
class CommandReceipt:
    """Content-free result of one adapter command attempt."""

    command_id: str
    accepted: bool
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class SnapshotRequired:
    """Typed reset outcome for a listener gap or withheld sensitive event."""

    reason: Literal["snapshot-required"] = "snapshot-required"


class AdapterProjectionError(RuntimeError):
    """Base class for stable, content-free adapter failures."""


class UnknownCriticalGatewayEvent(AdapterProjectionError):
    """A gateway event could not be safely represented in protocol v1."""

    def __init__(self) -> None:
        super().__init__("gateway-event-unavailable")
