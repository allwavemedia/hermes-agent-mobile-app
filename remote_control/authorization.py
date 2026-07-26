"""Capability-bound remote-control authorization policy."""

from collections.abc import Mapping
from typing import Any, Literal

from remote_control.protocol import remote_document_hash


Risk = Literal["low", "medium", "high"]
Disposition = Literal["reject", "retain-opaque"]
_MEDIUM_RISK_UNLOCK_MAX_AGE_MS = 5 * 60 * 1000


def authorize_remote_action(
    *,
    capability: Mapping[str, Any],
    capability_hash: str,
    method: str,
    online: bool,
    queue_if_offline: bool,
    foreground: bool,
    unlocked: bool,
    unlock_age_ms: int,
    biometric_proof_verified: bool = False,
) -> dict[str, bool | str]:
    """Authorize a UI action without granting authority beyond the capability."""

    if remote_document_hash(capability) != capability_hash:
        return {"authorized": False, "reason": "capability-stale"}

    methods = capability.get("methods")
    if not isinstance(methods, Mapping):
        return {"authorized": False, "reason": "method-unsupported"}
    method_capability = methods.get(method)
    if not isinstance(method_capability, Mapping):
        return {"authorized": False, "reason": "method-unsupported"}

    risk = method_capability.get("risk")
    if risk not in {"low", "medium", "high"}:
        return {"authorized": False, "reason": "method-unsupported"}

    if not foreground:
        return {"authorized": False, "reason": "app-background"}
    if not unlocked:
        return {"authorized": False, "reason": "app-locked"}

    if not online and (
        not queue_if_offline
        or method != "prompt.submit"
        or method_capability.get("offline") is not True
        or risk != "low"
    ):
        return {"authorized": False, "reason": "offline-queue-disallowed"}

    if risk == "medium" and not (
        0 <= unlock_age_ms <= _MEDIUM_RISK_UNLOCK_MAX_AGE_MS
    ):
        return {"authorized": False, "reason": "step-up-required"}
    if (risk == "high" or method_capability.get("biometric") is True) and (
        biometric_proof_verified is not True
    ):
        return {"authorized": False, "reason": "step-up-required"}

    return {"authorized": True, "risk": risk}


def unknown_message_disposition(
    *,
    kind: Literal["command", "event", "security"],
    critical: bool,
) -> Disposition:
    """Retain only unknown, non-critical events as opaque telemetry."""

    return "retain-opaque" if kind == "event" and not critical else "reject"
