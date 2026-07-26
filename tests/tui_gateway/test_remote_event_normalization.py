"""Behavior contracts for safe gateway-to-remote event normalization."""

from __future__ import annotations

import copy
import json
import threading
from typing import Any

import pytest

from remote_control.protocol import validate_remote_control_document
from tui_gateway.transport import SessionEventDelivery


SESSION_ID = "session-0001"
CAPABILITY_HASH = "sha256-" + "A" * 43


def _remote_api():
    import remote_control

    adapter_type = getattr(remote_control, "GatewaySessionAdapter", None)
    context_type = getattr(remote_control, "AdapterSessionContext", None)
    error_type = getattr(remote_control, "UnknownCriticalGatewayEvent", None)
    reset_type = getattr(remote_control, "SnapshotRequired", None)
    assert adapter_type is not None, "GatewaySessionAdapter must be exported"
    assert context_type is not None, "AdapterSessionContext must be exported"
    assert error_type is not None, "UnknownCriticalGatewayEvent must be exported"
    assert reset_type is not None, "SnapshotRequired must be exported"
    return adapter_type, context_type, error_type, reset_type


class _Subscription:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _Gateway:
    def __init__(self) -> None:
        self._sessions = {SESSION_ID: {"transport": object(), "history": []}}
        self.sinks = []
        self.subscriptions = []
        self.before_additional_subscribe = None

    def subscribe_session_events(
        self,
        session_id,
        subscriber_id,
        sink,
        *,
        max_queue,
    ):
        assert session_id == SESSION_ID
        assert max_queue == 8
        if self.sinks and self.before_additional_subscribe is not None:
            self.before_additional_subscribe()
        subscription = _Subscription()
        self.sinks.append(sink)
        self.subscriptions.append(subscription)
        return subscription

    def emit(self, delivery) -> None:
        for sink in list(self.sinks):
            sink(delivery)

    def emit_to_existing(self, delivery) -> None:
        for sink in list(self.sinks):
            sink(delivery)


def _adapter(*, reasoning_visible: bool = True, gateway=None):
    adapter_type, context_type, _, _ = _remote_api()
    context = context_type(
        computer_id="computer-0001",
        session_id=SESSION_ID,
        session_revision=7,
        capability_hash=CAPABILITY_HASH,
        active_run_id="run-0001",
        issued_at="2030-01-02T03:00:00Z",
        expires_at="2030-01-02T03:05:00Z",
        signature="S" * 32,
        reasoning_visible=reasoning_visible,
    )
    return adapter_type(
        gateway=gateway or _Gateway(),
        context=context,
        epoch="epoch-0001",
        now=lambda: "2030-01-02T03:04:05Z",
        event_id_factory=lambda seq: f"event-{seq:04d}",
    )


def _frame(
    kind: str,
    payload: dict | None = None,
    *,
    session_id: str = SESSION_ID,
    critical: bool = False,
):
    params: dict[str, Any] = {
        "session_id": session_id,
        "type": kind,
        "payload": copy.deepcopy(payload or {}),
    }
    if critical:
        params["critical"] = True
    return {
        "jsonrpc": "2.0",
        "method": "event",
        "params": params,
    }


KNOWN_EVENT_FIXTURES = [
    ("message.start", {}, "message.started", {}),
    ("message.delta", {"text": "hel"}, "message.delta", {"text": "hel"}),
    (
        "message.delta",
        {"text": "open C:/Users/alice/private/file.txt"},
        "message.delta",
        {"text": "open «redacted-path»"},
    ),
    (
        "message.delta",
        {"text": r"open /home/alice/private/file.txt and \\server\share\file.txt"},
        "message.delta",
        {"text": "open «redacted-path» and «redacted-path»"},
    ),
    (
        "message.delta",
        {"text": "open /tmp"},
        "message.delta",
        {"text": "open «redacted-path»"},
    ),
    (
        "message.interim",
        {"text": "draft", "already_streamed": False, "provider": "secret"},
        "message.interim",
        {"text": "draft", "alreadyStreamed": False},
    ),
    (
        "message.complete",
        {"text": "hello", "status": "complete", "rendered": "<secret>"},
        "message.completed",
        {"text": "hello", "status": "complete"},
    ),
    (
        "message.complete",
        {
            "text": "provider failed at /home/alice/private/provider.log",
            "status": "error",
        },
        "message.completed",
        {"text": "Unable to complete the request", "status": "error"},
    ),
    (
        "reasoning.available",
        {"text": "safe reasoning", "provider": "secret"},
        "reasoning.started",
        {"text": "safe reasoning"},
    ),
    (
        "reasoning.delta",
        {"text": "safe reasoning", "token": "secret"},
        "reasoning.delta",
        {"text": "safe reasoning"},
    ),
    (
        "tool.start",
        {
            "tool_id": "tool-0001",
            "name": "search",
            "context": "Search",
            "args_text": "Authorization: Bearer tool-arg-secret",
        },
        "tool.started",
        {"toolId": "tool-0001", "name": "search", "context": "Search"},
    ),
    (
        "tool.generating",
        {"name": "search"},
        "tool.progress",
        {"name": "search", "status": "generating"},
    ),
    (
        "tool.complete",
        {
            "tool_id": "tool-0001",
            "name": "search",
            "result": {"Authorization": "Bearer result-secret"},
            "result_text": "C:/private/output",
            "inline_diff": "secret diff",
        },
        "tool.completed",
        {
            "toolId": "tool-0001",
            "name": "search",
            "status": "complete",
            "summary": "Tool completed",
        },
    ),
    (
        "tool.complete",
        {"tool_id": "tool-0001", "name": "search", "status": "error"},
        "tool.failed",
        {
            "toolId": "tool-0001",
            "name": "search",
            "status": "error",
            "summary": "Tool failed",
        },
    ),
    (
        "tool.output_risk",
        {
            "tool_id": "tool-0001",
            "name": "web_extract",
            "risk": "high",
            "findings": ["prompt_injection"],
            "redacted": False,
            "output": "Authorization: Bearer output-secret",
        },
        "tool.risk",
        {
            "toolId": "tool-0001",
            "name": "web_extract",
            "risk": "high",
            "findings": ["prompt_injection"],
            "redacted": False,
        },
    ),
    (
        "approval.request",
        {
            "request_id": "request-0001",
            "choices": ["once", "session", "always", "deny"],
            "command": "Authorization: Bearer approval-command-secret",
        },
        "request.approval",
        {
            "requestId": "request-0001",
            "choices": ["approve_once", "deny"],
            "summary": "Approval required",
        },
    ),
    (
        "clarify.request",
        {
            "request_id": "request-0001",
            "question": "Which?",
            "choices": ["A", "B"],
            "callback": "secret",
        },
        "request.clarification",
        {
            "requestId": "request-0001",
            "question": "Which?",
            "choices": ["A", "B"],
        },
    ),
    (
        "terminal.read.request",
        {
            "request_id": "request-0001",
            "start": 0,
            "count": 10,
            "buffer": "terminal-secret",
        },
        "request.terminalRead",
        {"requestId": "request-0001", "start": 0, "count": 10},
    ),
    (
        "clarify.expire",
        {"request_id": "request-0001"},
        "request.expired",
        {"requestId": "request-0001", "requestKind": "clarification"},
    ),
    (
        "terminal.read.expire",
        {"request_id": "request-0001"},
        "request.expired",
        {"requestId": "request-0001", "requestKind": "terminalRead"},
    ),
    (
        "status.update",
        {"kind": "compacting", "text": "Summarizing", "exception": "secret"},
        "session.status",
        {"status": "compacting", "text": "Summarizing"},
    ),
    (
        "session.title",
        {"title": "Safe title", "path": "C:/private"},
        "session.title",
        {"title": "Safe title"},
    ),
    (
        "session.info",
        {
            "model": "test-model",
            "project": {
                "id": "project-0001",
                "name": "safe-project",
                "primary_path": "C:/private/project",
            },
            "cwd": "C:/private",
            "provider": "provider-secret",
            "tools": {"shell": True},
        },
        "session.context",
        {"model": "test-model", "project": "safe-project"},
    ),
    (
        "subagent.start",
        {
            "subagent_id": "agent-0001",
            "goal": "Safe goal",
            "files_read": ["C:/private"],
        },
        "subagent.started",
        {"subagentId": "agent-0001", "goal": "Safe goal", "status": "running"},
    ),
    (
        "subagent.tool",
        {
            "subagent_id": "agent-0001",
            "status": "working",
            "tool_name": "web_search",
            "text": "Searching",
            "output_tail": "secret output",
        },
        "subagent.updated",
        {
            "subagentId": "agent-0001",
            "status": "working",
            "toolName": "web_search",
            "summary": "Searching",
        },
    ),
    (
        "subagent.thinking",
        {"subagent_id": "agent-0001", "text": "Considering"},
        "subagent.updated",
        {"subagentId": "agent-0001", "status": "thinking", "summary": "Considering"},
    ),
    (
        "subagent.complete",
        {
            "subagent_id": "agent-0001",
            "status": "complete",
            "summary": "Done",
            "files_written": ["C:/private"],
        },
        "subagent.completed",
        {"subagentId": "agent-0001", "status": "complete", "summary": "Done"},
    ),
    (
        "error",
        {
            "message": "provider-secret failed at C:/Users/alice/private/provider.log",
            "traceback": "secret traceback",
        },
        "session.status",
        {"status": "failed", "reason": "internal-unavailable"},
    ),
]


@pytest.mark.parametrize(
    ("kind", "payload", "expected_type", "expected_data"),
    KNOWN_EVENT_FIXTURES,
)
def test_known_gateway_events_normalize_to_schema_v1(
    kind,
    payload,
    expected_type,
    expected_data,
):
    event = _adapter().normalize_event(_frame(kind, payload))

    assert event is not None
    assert validate_remote_control_document("event", event).valid
    assert event == {
        "seq": 1,
        "prevSeq": 0,
        "eventId": "event-0001",
        "occurredAt": "2030-01-02T03:04:05Z",
        "eventType": expected_type,
        "data": expected_data,
    }
    serialized = json.dumps(event)
    for forbidden in (
        "provider-secret",
        "tool-arg-secret",
        "result-secret",
        "output-secret",
        "approval-command-secret",
        "terminal-secret",
        "C:/private",
        "C:/Users/alice",
        "/home/alice",
        "secret diff",
        "output_tail",
        "files_read",
        "files_written",
        "traceback",
    ):
        assert forbidden not in serialized


def test_sequence_is_contiguous_and_unknown_or_hidden_events_consume_no_sequence():
    adapter = _adapter(reasoning_visible=False)

    assert adapter.normalize_event(_frame("notification.show", {"text": "UI only"})) is None
    assert adapter.normalize_event(_frame("reasoning.delta", {"text": "hidden"})) is None
    first = adapter.normalize_event(_frame("message.delta", {"text": "one"}))
    second = adapter.normalize_event(_frame("message.complete", {"text": "two"}))

    assert (first["seq"], first["prevSeq"], first["eventId"]) == (
        1,
        0,
        "event-0001",
    )
    assert (second["seq"], second["prevSeq"], second["eventId"]) == (
        2,
        1,
        "event-0002",
    )


def test_unknown_critical_sensitive_or_wrong_session_events_fail_closed_without_sequence():
    _, _, error_type, _ = _remote_api()
    adapter = _adapter()

    with pytest.raises(error_type) as critical:
        adapter.normalize_event(
            _frame("security.policy.changed", {"secret": "credential"}),
            critical=True,
        )
    with pytest.raises(error_type) as sensitive:
        adapter.normalize_event(
            _frame("agent.terminal.output", {"chunk": "terminal secret"}),
        )
    with pytest.raises(error_type) as wrong_session:
        adapter.normalize_event(
            _frame("message.delta", {"text": "other"}, session_id="session-9999"),
        )

    assert str(critical.value) == "gateway-event-unavailable"
    assert str(sensitive.value) == "gateway-event-unavailable"
    assert str(wrong_session.value) == "gateway-event-unavailable"
    first = adapter.normalize_event(_frame("message.delta", {"text": "safe"}))
    assert first["seq"] == 1


def test_malformed_frames_fail_closed_without_leaking_input_or_consuming_sequence():
    _, _, error_type, _ = _remote_api()
    adapter = _adapter()
    malformed = [
        {"jsonrpc": "2.0", "id": "response", "result": {"secret": "x"}},
        {"jsonrpc": "2.0", "method": "event", "params": {}},
        _frame("message.delta", {"text": {"secret": "x"}}),
    ]

    for frame in malformed:
        with pytest.raises(error_type) as rejected:
            adapter.normalize_event(frame)
        assert str(rejected.value) == "gateway-event-unavailable"

    assert adapter.normalize_event(_frame("message.start"))["seq"] == 1


def test_subscription_consumes_listener_copies_preserves_transport_and_maps_reset():
    _, _, _, reset_type = _remote_api()
    gateway = _Gateway()
    original_transport = gateway._sessions[SESSION_ID]["transport"]
    adapter = _adapter(gateway=gateway)
    received = []

    subscription_id = adapter.subscribe(
        SESSION_ID,
        "mobile-0001",
        after_seq=0,
        sink=received.append,
        max_queue=8,
    )
    assert len(gateway.sinks) == 1
    gateway.emit(
        SessionEventDelivery(
            kind="event",
            session_id=SESSION_ID,
            frame=_frame("message.delta", {"text": "copied"}),
        )
    )
    gateway.emit(
        SessionEventDelivery(
            kind="reset-required",
            session_id=SESSION_ID,
            reason="queue-overflow-with-secret",
        )
    )

    assert validate_remote_control_document("event", received[0]).valid
    assert received[0]["data"] == {"text": "copied"}
    assert isinstance(received[1], reset_type)
    assert received[1].reason == "snapshot-required"
    assert "secret" not in repr(received[1])
    assert gateway._sessions[SESSION_ID]["transport"] is original_transport
    assert gateway.subscriptions[0].closed is True

    adapter.close_subscription(subscription_id)
    adapter.subscribe(
        SESSION_ID,
        "mobile-0002",
        after_seq=1,
        sink=received.append,
        max_queue=8,
    )
    assert len(gateway.subscriptions) == 2


def test_subscribers_share_one_normalized_event_identity_and_one_upstream_copy():
    gateway = _Gateway()
    adapter = _adapter(gateway=gateway)
    first = []
    second = []

    adapter.subscribe(
        SESSION_ID,
        "mobile-0001",
        after_seq=0,
        sink=first.append,
        max_queue=8,
    )
    adapter.subscribe(
        SESSION_ID,
        "mobile-0002",
        after_seq=0,
        sink=second.append,
        max_queue=8,
    )
    gateway.emit(
        SessionEventDelivery(
            kind="event",
            session_id=SESSION_ID,
            frame=_frame("message.delta", {"text": "shared"}),
        )
    )

    assert len(gateway.sinks) == 1
    assert first == second
    assert first[0]["seq"] == 1
    assert first[0]["eventId"] == "event-0001"


def test_subscription_cursor_establishment_never_misses_a_committed_event():
    gateway = _Gateway()
    adapter = _adapter(gateway=gateway)
    first = []
    second = []
    committed = threading.Event()

    adapter.subscribe(
        SESSION_ID,
        "mobile-0001",
        after_seq=0,
        sink=first.append,
        max_queue=8,
    )
    delivery = SessionEventDelivery(
        kind="event",
        session_id=SESSION_ID,
        frame=_frame("message.delta", {"text": "during-subscribe"}),
    )

    def commit_before_additional_registration() -> None:
        gateway.emit_to_existing(delivery)
        committed.set()

    gateway.before_additional_subscribe = commit_before_additional_registration
    reset_required = False
    try:
        adapter.subscribe(
            SESSION_ID,
            "mobile-0002",
            after_seq=0,
            sink=second.append,
            max_queue=8,
        )
    except Exception as exc:
        reset_required = str(exc) == "snapshot-required"

    assert not (committed.is_set() and not reset_required and not second)


def test_subscription_preserves_critical_metadata_and_fails_closed():
    _, _, _, reset_type = _remote_api()
    gateway = _Gateway()
    adapter = _adapter(gateway=gateway)
    received = []
    adapter.subscribe(
        SESSION_ID,
        "mobile-0001",
        after_seq=0,
        sink=received.append,
        max_queue=8,
    )

    gateway.emit(
        SessionEventDelivery(
            kind="event",
            session_id=SESSION_ID,
            frame=_frame(
                "future.lifecycle",
                {"provider": "secret"},
                critical=True,
            ),
        )
    )

    assert len(received) == 1
    assert isinstance(received[0], reset_type)
    assert received[0].reason == "snapshot-required"
    assert "secret" not in repr(received[0])
