"""Stable, allowlisted projection over the internal TUI gateway session API."""

from __future__ import annotations

import copy
import re
import threading
import uuid
from collections.abc import Callable, Mapping
from contextlib import nullcontext
from typing import Any, Final, cast

from agent.redact import redact_sensitive_text

from remote_control.models import (
    AdapterProjectionError,
    AdapterSessionContext,
    CommandReceipt,
    RemoteCommandActor,
    SnapshotRequired,
    UnknownCriticalGatewayEvent,
)
from remote_control.protocol import validate_remote_control_document


_COMMAND_FIELDS: Final[dict[str, frozenset[str]]] = {
    "prompt.submit": frozenset({"commandType", "text", "queueIfOffline"}),
    "session.steer": frozenset({"commandType", "activeRunId", "text"}),
    "session.interrupt": frozenset({"commandType", "activeRunId"}),
}
_SENSITIVE_EVENT_PREFIXES: Final = (
    "approval.",
    "attachment.",
    "capabilities.",
    "security.",
    "secret.",
    "sudo.",
    "terminal.",
)
_SENSITIVE_EVENT_KINDS: Final = frozenset({"agent.terminal.output"})
_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_WINDOWS_ABSOLUTE_RE: Final = re.compile(r"^[A-Za-z]:")
_WINDOWS_PATH_RE: Final = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/][^ \t\r\n<>'\"]+)"
)
_UNC_PATH_RE: Final = re.compile(
    r"(?<![\\A-Za-z0-9])\\\\[^\\\s<>'\"]+\\[^ \t\r\n<>'\"]+"
)
_POSIX_PATH_RE: Final = re.compile(
    r"(?<![:/A-Za-z0-9])/(?:[^/\s<>'\"]+/)*[^/\s<>'\"]+"
)


def _bounded_utf8(value: str, max_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def _safe_text(value: object, *, max_bytes: int = 4096) -> str:
    if not isinstance(value, str):
        raise AdapterProjectionError("gateway-event-unavailable")
    try:
        redacted = redact_sensitive_text(value, force=True)
    except Exception:
        return "content unavailable"
    without_paths = _WINDOWS_PATH_RE.sub("«redacted-path»", str(redacted))
    without_paths = _UNC_PATH_RE.sub("«redacted-path»", without_paths)
    without_paths = _POSIX_PATH_RE.sub("«redacted-path»", without_paths)
    return _bounded_utf8(without_paths, max_bytes)


def _optional_text(
    payload: Mapping[str, Any],
    key: str,
    *,
    max_bytes: int = 4096,
) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    return _safe_text(value, max_bytes=max_bytes)


def _safe_identifier(value: object, *, fallback: str | None = None) -> str:
    if isinstance(value, str) and _IDENTIFIER_RE.fullmatch(value):
        return value
    if fallback is not None:
        return fallback
    raise AdapterProjectionError("gateway-event-unavailable")


def _safe_label(value: object, *, max_bytes: int = 256) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if (
        "/" in value
        or "\\" in value
        or _WINDOWS_ABSOLUTE_RE.match(value)
        or any(ord(char) < 32 for char in value)
    ):
        return None
    return _safe_text(value, max_bytes=max_bytes)


def _safe_choices(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        _safe_text(choice, max_bytes=256)
        for choice in value[:32]
        if isinstance(choice, str)
    ]


class GatewaySessionAdapter:
    """Project one authenticated live session into remote-control protocol v1."""

    def __init__(
        self,
        *,
        gateway: Any,
        context: AdapterSessionContext,
        epoch: str,
        now: Callable[[], str],
        event_id_factory: Callable[[int], str],
    ) -> None:
        self._gateway = gateway
        self._context = context
        self._epoch = epoch
        self._now = now
        self._event_id_factory = event_id_factory
        self._sequence = 0
        self._sequence_lock = threading.Lock()
        self._subscriptions: dict[
            str,
            Callable[[dict[str, Any] | SnapshotRequired], None],
        ] = {}
        self._subscriptions_lock = threading.Lock()
        self._upstream_subscription: Any | None = None
        self._upstream_lock = threading.Lock()

    def _session(self, session_id: str) -> Mapping[str, Any]:
        if session_id != self._context.session_id:
            raise AdapterProjectionError("session-unavailable")
        sessions = getattr(self._gateway, "_sessions", None)
        if not isinstance(sessions, dict):
            raise AdapterProjectionError("session-unavailable")
        session = sessions.get(session_id)
        if not isinstance(session, Mapping):
            raise AdapterProjectionError("session-unavailable")
        return session

    def get_capabilities(self, session_id: str) -> dict[str, Any]:
        """Return a fresh three-method capability projection."""

        self._session(session_id)
        context = self._context
        capability = {
            "capabilityVersion": 1,
            "computerId": context.computer_id,
            "sessionId": context.session_id,
            "sessionRevision": context.session_revision,
            "issuedAt": context.issued_at,
            "expiresAt": context.expires_at,
            "methods": {
                "prompt.submit": {
                    "risk": "low",
                    "offline": False,
                    "biometric": False,
                    "maxBytes": 65536,
                },
                "session.steer": {
                    "risk": "medium",
                    "offline": False,
                    "biometric": False,
                    "maxBytes": 65536,
                },
                "session.interrupt": {
                    "risk": "medium",
                    "offline": False,
                    "biometric": False,
                },
            },
            "constraints": {
                "terminalRead": False,
                "terminalWrite": False,
                "reasoningVisible": context.reasoning_visible,
            },
            "signature": context.signature,
        }
        if not validate_remote_control_document("capability", capability).valid:
            raise AdapterProjectionError("capability-unavailable")
        return capability

    def get_snapshot(self, session_id: str) -> dict[str, Any]:
        """Build a fresh schema-valid snapshot without internal gateway fields."""

        session = self._session(session_id)
        lock = session.get("history_lock")
        lock_context = lock if hasattr(lock, "__enter__") else nullcontext()
        with self._sequence_lock:
            with lock_context:
                history = list(session.get("history") or [])
                pending = list(session.get("pending_requests") or [])
                running = bool(session.get("running"))
                inflight = session.get("inflight_turn")
                title = _safe_text(session.get("title") or "", max_bytes=256)
                project = _safe_label(
                    session.get("project_label") or session.get("project")
                )
                model = _safe_label(
                    session.get("model_override") or session.get("model"),
                    max_bytes=128,
                )

            transcript = self._project_transcript(history)
            pending_requests = self._project_pending_requests(pending)
            status = self._snapshot_status(
                running=running,
                inflight=inflight,
                has_pending_requests=bool(pending),
            )
            session_projection: dict[str, Any] = {
                "id": self._context.session_id,
                "title": title,
                "status": status,
                "activeRunId": self._context.active_run_id,
            }
            if project is not None:
                session_projection["project"] = project
                session_projection["cwdLabel"] = project
            if model is not None:
                session_projection["model"] = model

            snapshot = {
                "epoch": self._epoch,
                "snapshotSeq": self._sequence,
                "sessionRevision": self._context.session_revision,
                "generatedAt": self._now(),
                "session": session_projection,
                "transcript": transcript,
                "activities": [],
                "pendingRequests": pending_requests,
                "terminals": [],
                "attachments": [],
                "capabilityHash": self._context.capability_hash,
            }
            if not validate_remote_control_document("snapshot", snapshot).valid:
                raise AdapterProjectionError("snapshot-unavailable")
            return snapshot

    def _project_transcript(self, history: list[Any]) -> list[dict[str, Any]]:
        transcript = []
        for source in history[:10000]:
            if not isinstance(source, Mapping):
                continue
            role = source.get("role")
            if role not in {"user", "assistant"}:
                continue
            content = source.get("content")
            if not isinstance(content, str):
                continue
            item: dict[str, Any] = {
                "id": f"message-{len(transcript) + 1:04d}",
                "type": "message",
                "role": role,
                "text": _safe_text(content, max_bytes=65536),
            }
            if self._context.reasoning_visible and role == "assistant":
                reasoning = source.get("reasoning")
                if isinstance(reasoning, str):
                    item["reasoning"] = _safe_text(reasoning, max_bytes=65536)
            transcript.append(item)
        return transcript

    def _project_pending_requests(self, pending: list[Any]) -> list[dict[str, Any]]:
        projected = []
        for source in pending[:100]:
            if not isinstance(source, Mapping):
                continue
            request_type = source.get("type")
            request_id = source.get("request_id")
            if request_type != "clarification":
                continue
            try:
                safe_request_id = _safe_identifier(request_id)
                question = _safe_text(source.get("question"), max_bytes=4096)
            except AdapterProjectionError:
                continue
            projected.append(
                {
                    "id": safe_request_id,
                    "type": "clarification",
                    "requestId": safe_request_id,
                    "question": question,
                    "choices": _safe_choices(source.get("choices")),
                }
            )
        return projected

    @staticmethod
    def _snapshot_status(
        *,
        running: bool,
        inflight: object,
        has_pending_requests: bool,
    ) -> str:
        if isinstance(inflight, Mapping):
            inflight_map = cast(Mapping[str, Any], inflight)
            if inflight_map.get("status") == "error":
                return "failed"
        if has_pending_requests:
            return "waiting"
        return "running" if running else "idle"

    def execute(
        self,
        command: Mapping[str, Any],
        *,
        actor: RemoteCommandActor,
    ) -> CommandReceipt:
        """Validate bindings and invoke one exact gateway command mapping."""

        command_id = f"command-{uuid.uuid4()}"
        command_type = command.get("commandType") if isinstance(command, Mapping) else None
        allowed_fields = _COMMAND_FIELDS.get(command_type) if isinstance(command_type, str) else None
        if allowed_fields is None or set(command) != allowed_fields:
            return CommandReceipt(command_id, False, "method-unsupported")

        if actor.authenticated_session_id != self._context.session_id:
            return CommandReceipt(command_id, False, "session-mismatch")
        if actor.session_revision != self._context.session_revision:
            return CommandReceipt(command_id, False, "session-revision-mismatch")
        if actor.capability_hash != self._context.capability_hash:
            return CommandReceipt(command_id, False, "capability-stale")

        if command_type == "prompt.submit":
            text = command.get("text")
            if (
                not isinstance(text, str)
                or not text
                or len(text.encode("utf-8")) > 65536
                or not isinstance(command.get("queueIfOffline"), bool)
            ):
                return CommandReceipt(command_id, False, "method-unsupported")
            if command.get("queueIfOffline") is True:
                return CommandReceipt(command_id, False, "queue-disallowed")
            params = {"session_id": self._context.session_id, "text": text}
        else:
            if (
                command.get("activeRunId") != self._context.active_run_id
                or self._context.active_run_id is None
            ):
                return CommandReceipt(command_id, False, "session-run-mismatch")
            if command_type == "session.steer":
                text = command.get("text")
                if (
                    not isinstance(text, str)
                    or not text
                    or len(text.encode("utf-8")) > 65536
                ):
                    return CommandReceipt(command_id, False, "method-unsupported")
                params = {"session_id": self._context.session_id, "text": text}
            else:
                params = {"session_id": self._context.session_id}

        try:
            response = self._gateway.invoke_remote_session_command(
                command_type,
                command_id,
                params,
            )
        except Exception:
            return CommandReceipt(command_id, False, "internal-unavailable")
        if not isinstance(response, Mapping) or "error" in response:
            return CommandReceipt(command_id, False, "internal-unavailable")
        return CommandReceipt(command_id, True)

    def normalize_event(
        self,
        frame: Mapping[str, Any],
        *,
        critical: bool = False,
    ) -> dict[str, Any] | None:
        """Map one copied internal event to a fresh ordered v1 event."""

        try:
            if frame.get("method") != "event":
                raise UnknownCriticalGatewayEvent
            params = frame.get("params")
            if not isinstance(params, Mapping):
                raise UnknownCriticalGatewayEvent
            if params.get("session_id") != self._context.session_id:
                raise UnknownCriticalGatewayEvent
            kind = params.get("type")
            payload = params.get("payload", {})
            if not isinstance(kind, str) or not isinstance(payload, Mapping):
                raise UnknownCriticalGatewayEvent
            critical = critical or params.get("critical") is True
            projected = self._project_event(kind, payload)
        except UnknownCriticalGatewayEvent:
            raise
        except AdapterProjectionError as exc:
            raise UnknownCriticalGatewayEvent from exc

        if projected is None:
            if (
                critical
                or kind in _SENSITIVE_EVENT_KINDS
                or kind.startswith(_SENSITIVE_EVENT_PREFIXES)
            ):
                raise UnknownCriticalGatewayEvent
            return None
        event_type, data = projected

        with self._sequence_lock:
            seq = self._sequence + 1
            event = {
                "seq": seq,
                "prevSeq": self._sequence,
                "eventId": self._event_id_factory(seq),
                "occurredAt": self._now(),
                "eventType": event_type,
                "data": data,
            }
            if not validate_remote_control_document("event", event).valid:
                raise UnknownCriticalGatewayEvent
            self._sequence = seq
        return event

    def _project_event(
        self,
        kind: str,
        payload: Mapping[str, Any],
    ) -> tuple[str, dict[str, Any]] | None:
        if kind == "message.start":
            return "message.started", {}
        if kind == "message.delta":
            return "message.delta", {"text": _safe_text(payload.get("text"))}
        if kind == "message.interim":
            return (
                "message.interim",
                {
                    "text": _safe_text(payload.get("text")),
                    "alreadyStreamed": bool(payload.get("already_streamed", False)),
                },
            )
        if kind == "message.complete":
            status = _safe_text(payload.get("status") or "complete", max_bytes=64)
            return (
                "message.completed",
                {
                    "text": (
                        "Unable to complete the request"
                        if status in {"error", "failed"}
                        else _safe_text(payload.get("text"))
                    ),
                    "status": status,
                },
            )
        if kind in {"reasoning.available", "reasoning.delta", "thinking.delta"}:
            if not self._context.reasoning_visible:
                return None
            event_type = "reasoning.started" if kind == "reasoning.available" else "reasoning.delta"
            return event_type, {"text": _safe_text(payload.get("text"))}
        if kind == "tool.start":
            data = self._tool_identity(payload)
            context = _optional_text(payload, "context", max_bytes=256)
            if context is not None:
                data["context"] = context
            return "tool.started", data
        if kind == "tool.generating":
            return (
                "tool.progress",
                {
                    "name": _safe_text(payload.get("name"), max_bytes=128),
                    "status": "generating",
                },
            )
        if kind == "tool.complete":
            data = self._tool_identity(payload)
            failed = payload.get("status") == "error"
            data.update(
                {
                    "status": "error" if failed else "complete",
                    "summary": "Tool failed" if failed else "Tool completed",
                }
            )
            return ("tool.failed" if failed else "tool.completed"), data
        if kind == "tool.output_risk":
            data = self._tool_identity(payload)
            risk = payload.get("risk")
            if risk not in {"low", "medium", "high"}:
                raise AdapterProjectionError("gateway-event-unavailable")
            data["risk"] = risk
            data["findings"] = _safe_choices(payload.get("findings"))
            data["redacted"] = bool(payload.get("redacted", False))
            return "tool.risk", data
        if kind == "approval.request":
            return (
                "request.approval",
                {
                    "requestId": _safe_identifier(payload.get("request_id")),
                    "choices": ["approve_once", "deny"],
                    "summary": "Approval required",
                },
            )
        if kind == "clarify.request":
            return (
                "request.clarification",
                {
                    "requestId": _safe_identifier(payload.get("request_id")),
                    "question": _safe_text(payload.get("question")),
                    "choices": _safe_choices(payload.get("choices")),
                },
            )
        if kind == "terminal.read.request":
            start = payload.get("start")
            count = payload.get("count")
            if not isinstance(start, int) or not isinstance(count, int):
                raise AdapterProjectionError("gateway-event-unavailable")
            return (
                "request.terminalRead",
                {
                    "requestId": _safe_identifier(payload.get("request_id")),
                    "start": max(0, start),
                    "count": max(0, min(count, 10000)),
                },
            )
        if kind in {"clarify.expire", "terminal.read.expire"}:
            return (
                "request.expired",
                {
                    "requestId": _safe_identifier(payload.get("request_id")),
                    "requestKind": (
                        "clarification" if kind == "clarify.expire" else "terminalRead"
                    ),
                },
            )
        if kind == "status.update":
            return (
                "session.status",
                {
                    "status": _safe_text(payload.get("kind") or "status", max_bytes=80),
                    "text": _safe_text(payload.get("text") or payload.get("kind"), max_bytes=4096),
                },
            )
        if kind == "session.title":
            return "session.title", {"title": _safe_text(payload.get("title"), max_bytes=256)}
        if kind == "session.info":
            data: dict[str, Any] = {}
            model = _safe_label(payload.get("model"), max_bytes=128)
            raw_project = payload.get("project")
            if isinstance(raw_project, Mapping):
                raw_project = raw_project.get("name")
            project = _safe_label(raw_project, max_bytes=256)
            if model is not None:
                data["model"] = model
            if project is not None:
                data["project"] = project
            return "session.context", data
        if kind in {"subagent.start", "subagent.tool", "subagent.thinking", "subagent.complete"}:
            subagent_id = _safe_identifier(
                payload.get("id") or payload.get("subagent_id")
            )
            if kind == "subagent.start":
                return (
                    "subagent.started",
                    {
                        "subagentId": subagent_id,
                        "goal": _safe_text(payload.get("goal"), max_bytes=4096),
                        "status": "running",
                    },
                )
            status = (
                "thinking"
                if kind == "subagent.thinking"
                else _safe_text(payload.get("status") or "working", max_bytes=80)
            )
            data = {"subagentId": subagent_id, "status": status}
            summary = _optional_text(payload, "summary", max_bytes=4096)
            if summary is None:
                summary = _optional_text(payload, "text", max_bytes=4096)
            if kind == "subagent.tool":
                tool_name = _optional_text(payload, "tool_name", max_bytes=128)
                if tool_name is not None:
                    data["toolName"] = tool_name
            if summary is not None:
                data["summary"] = summary
            return (
                "subagent.completed" if kind == "subagent.complete" else "subagent.updated",
                data,
            )
        if kind == "error":
            return (
                "session.status",
                {
                    "status": "failed",
                    "reason": "internal-unavailable",
                },
            )
        return None

    @staticmethod
    def _tool_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "toolId": _safe_identifier(payload.get("tool_id")),
            "name": _safe_text(payload.get("name"), max_bytes=128),
        }

    def subscribe(
        self,
        session_id: str,
        subscriber_id: str,
        after_seq: int,
        sink: Callable[[dict[str, Any] | SnapshotRequired], None],
        *,
        max_queue: int = 256,
    ) -> str:
        """Subscribe to copied Task 4 deliveries without changing transport."""

        self._session(session_id)
        subscription_id = f"{session_id}:{subscriber_id}"
        self._ensure_upstream_subscription(max_queue=max_queue)

        with self._sequence_lock:
            if after_seq != self._sequence:
                raise AdapterProjectionError("snapshot-required")
            with self._subscriptions_lock:
                if subscription_id in self._subscriptions:
                    raise AdapterProjectionError("subscription-unavailable")
                self._subscriptions[subscription_id] = sink
        return subscription_id

    def close_subscription(self, subscription_id: str) -> None:
        """Close one adapter-owned subscription idempotently."""

        with self._subscriptions_lock:
            self._subscriptions.pop(subscription_id, None)

    def _ensure_upstream_subscription(self, *, max_queue: int) -> None:
        with self._upstream_lock:
            if self._upstream_subscription is not None:
                return
            self._upstream_subscription = self._gateway.subscribe_session_events(
                self._context.session_id,
                f"remote-adapter:{self._context.session_id}",
                self._on_upstream_delivery,
                max_queue=max_queue,
            )

    def _on_upstream_delivery(self, delivery: Any) -> None:
        if (
            getattr(delivery, "kind", None) == "reset-required"
            and getattr(delivery, "session_id", None) == self._context.session_id
        ):
            self._invalidate_upstream_subscription()
            self._fan_out(SnapshotRequired())
            return
        if (
            getattr(delivery, "kind", None) != "event"
            or getattr(delivery, "session_id", None) != self._context.session_id
            or not isinstance(getattr(delivery, "frame", None), Mapping)
        ):
            self._fan_out(SnapshotRequired())
            return
        try:
            event = self.normalize_event(delivery.frame)
        except UnknownCriticalGatewayEvent:
            self._fan_out(SnapshotRequired())
            return
        if event is not None:
            self._fan_out(event)

    def _invalidate_upstream_subscription(self) -> None:
        with self._upstream_lock:
            subscription = self._upstream_subscription
            self._upstream_subscription = None
        if subscription is not None:
            subscription.close()

    def _fan_out(self, outcome: dict[str, Any] | SnapshotRequired) -> None:
        with self._subscriptions_lock:
            sinks = list(self._subscriptions.values())
        for sink in sinks:
            delivered = copy.deepcopy(outcome) if isinstance(outcome, dict) else outcome
            try:
                sink(delivered)
            except Exception:
                continue
