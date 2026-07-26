"""Behavior contracts for the stable remote gateway session adapter."""

from __future__ import annotations

import copy
import json
import threading
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from remote_control.protocol import validate_remote_control_document
from tui_gateway.transport import Transport


SESSION_ID = "session-0001"
CAPABILITY_HASH = "sha256-" + "A" * 43


def _remote_api():
    import remote_control

    adapter_type = getattr(remote_control, "GatewaySessionAdapter", None)
    context_type = getattr(remote_control, "AdapterSessionContext", None)
    actor_type = getattr(remote_control, "RemoteCommandActor", None)
    assert adapter_type is not None, "GatewaySessionAdapter must be exported"
    assert context_type is not None, "AdapterSessionContext must be exported"
    assert actor_type is not None, "RemoteCommandActor must be exported"
    return adapter_type, context_type, actor_type


def _context(*, reasoning_visible: bool = False, active_run_id: str | None = "run-0001"):
    _, context_type, _ = _remote_api()
    return context_type(
        computer_id="computer-0001",
        session_id=SESSION_ID,
        session_revision=7,
        capability_hash=CAPABILITY_HASH,
        active_run_id=active_run_id,
        issued_at="2030-01-02T03:00:00Z",
        expires_at="2030-01-02T03:05:00Z",
        signature="S" * 32,
        reasoning_visible=reasoning_visible,
    )


def _actor(context=None):
    _, _, actor_type = _remote_api()
    current = context or _context()
    return actor_type(
        authenticated_session_id=current.session_id,
        session_revision=current.session_revision,
        capability_hash=current.capability_hash,
    )


def _adapter(gateway, *, context=None):
    adapter_type, _, _ = _remote_api()
    return adapter_type(
        gateway=gateway,
        context=context or _context(),
        epoch="epoch-0001",
        now=lambda: "2030-01-02T03:04:05Z",
        event_id_factory=lambda seq: f"event-{seq:04d}",
    )


class _RecordingGateway:
    def __init__(self, session: dict | None = None) -> None:
        self._sessions = {SESSION_ID: session or {}}
        self.calls: list[tuple[str, str, dict]] = []
        self.response: dict = {
            "jsonrpc": "2.0",
            "id": "remote-command",
            "result": {"status": "accepted"},
        }

    def invoke_remote_session_command(
        self,
        command_type: str,
        request_id: str,
        params: dict,
    ) -> dict:
        self.calls.append((command_type, request_id, copy.deepcopy(params)))
        return copy.deepcopy(self.response)


def _session_fixture() -> dict:
    return {
        "history_lock": threading.RLock(),
        "history": [
            {"role": "system", "content": "provider secret system prompt"},
            {"role": "user", "content": "hello"},
            {
                "role": "assistant",
                "content": "safe answer",
                "reasoning": "Authorization: Bearer reasoning-secret",
                "tool_calls": [{"function": {"arguments": '{"token":"raw"}'}}],
            },
            {
                "role": "tool",
                "content": "Authorization: Bearer tool-result-secret",
            },
        ],
        "title": "Safe title",
        "project_label": "private-workspace",
        "model_override": "test-model",
        "running": False,
        "inflight_turn": None,
        "agent": SimpleNamespace(api_key="host-api-key"),
        "transport": object(),
        "session_key": "stored-private-key",
        "cwd": "C:/Users/alice/private-workspace",
        "approval": {"token": "approval-secret"},
        "pending_requests": [
            {
                "type": "clarification",
                "request_id": "request-0001",
                "question": "Which safe option?",
                "choices": ["A", "B"],
                "command": "Authorization: Bearer pending-secret",
            }
        ],
    }


def test_snapshot_and_capabilities_are_fresh_schema_valid_allowlisted_projections():
    source = _session_fixture()
    gateway = _RecordingGateway(source)
    adapter = _adapter(gateway)

    snapshot = adapter.get_snapshot(SESSION_ID)
    capabilities = adapter.get_capabilities(SESSION_ID)

    assert validate_remote_control_document("snapshot", snapshot).valid
    assert validate_remote_control_document("capability", capabilities).valid
    assert snapshot["epoch"] == "epoch-0001"
    assert snapshot["snapshotSeq"] == 0
    assert snapshot["sessionRevision"] == 7
    assert snapshot["generatedAt"] == "2030-01-02T03:04:05Z"
    assert snapshot["capabilityHash"] == CAPABILITY_HASH
    assert snapshot["session"] == {
        "id": SESSION_ID,
        "title": "Safe title",
        "project": "private-workspace",
        "cwdLabel": "private-workspace",
        "model": "test-model",
        "status": "waiting",
        "activeRunId": "run-0001",
    }
    assert [(item["role"], item["text"]) for item in snapshot["transcript"]] == [
        ("user", "hello"),
        ("assistant", "safe answer"),
    ]
    assert snapshot["activities"] == []
    assert snapshot["pendingRequests"] == [
        {
            "id": "request-0001",
            "type": "clarification",
            "requestId": "request-0001",
            "question": "Which safe option?",
            "choices": ["A", "B"],
        }
    ]
    assert snapshot["terminals"] == []
    assert snapshot["attachments"] == []
    assert capabilities["methods"] == {
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
    }
    assert capabilities["constraints"] == {
        "terminalRead": False,
        "terminalWrite": False,
        "reasoningVisible": False,
    }

    serialized = json.dumps({"snapshot": snapshot, "capabilities": capabilities})
    for forbidden in (
        "provider secret system prompt",
        "host-api-key",
        "approval-secret",
        "stored-private-key",
        "C:/Users/alice/private-workspace",
        "reasoning-secret",
        "tool-result-secret",
        "pending-secret",
        "tool_calls",
        "arguments",
        "transport",
        "api_key",
        '"token"',
    ):
        assert forbidden not in serialized
    assert source["transport"] is gateway._sessions[SESSION_ID]["transport"]


@pytest.mark.parametrize(
    ("session_patch", "expected"),
    [
        ({"running": False, "inflight_turn": None, "pending_requests": []}, "idle"),
        ({"running": True, "inflight_turn": None, "pending_requests": []}, "running"),
        (
            {
                "running": True,
                "inflight_turn": None,
                "pending_requests": [{"type": "clarification", "request_id": "request-1"}],
            },
            "waiting",
        ),
        (
            {
                "running": False,
                "inflight_turn": {"status": "error", "error": "provider secret"},
                "pending_requests": [],
            },
            "failed",
        ),
    ],
)
def test_snapshot_derives_only_protocol_session_statuses(session_patch, expected):
    session = _session_fixture()
    session.update(session_patch)
    snapshot = _adapter(_RecordingGateway(session)).get_snapshot(SESSION_ID)
    assert snapshot["session"]["status"] == expected


def test_snapshot_cursor_cannot_advance_after_snapshot_content_is_copied():
    session = _session_fixture()
    gateway = _RecordingGateway(session)
    adapter = _adapter(gateway)
    started = threading.Event()
    finished = threading.Event()
    normalized = []

    def commit_event() -> None:
        started.set()
        normalized.append(
            adapter.normalize_event(
                {
                    "jsonrpc": "2.0",
                    "method": "event",
                    "params": {
                        "session_id": SESSION_ID,
                        "type": "message.delta",
                        "payload": {"text": "committed after copy"},
                    },
                }
            )
        )
        finished.set()

    class EventAfterHistoryCopy:
        committed_before_release = False
        worker: threading.Thread | None = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            self.worker = threading.Thread(target=commit_event)
            self.worker.start()
            assert started.wait(timeout=1)
            self.committed_before_release = finished.wait(timeout=0.2)
            return False

    history_lock = EventAfterHistoryCopy()
    session["history_lock"] = history_lock

    snapshot = adapter.get_snapshot(SESSION_ID)
    assert history_lock.worker is not None
    history_lock.worker.join(timeout=1)

    assert history_lock.committed_before_release is False
    assert snapshot["snapshotSeq"] == 0
    assert normalized[0]["seq"] == 1


@pytest.mark.parametrize(
    ("command", "expected_params"),
    [
        (
            {"commandType": "prompt.submit", "text": "hello", "queueIfOffline": False},
            {"session_id": SESSION_ID, "text": "hello"},
        ),
        (
            {
                "commandType": "session.steer",
                "activeRunId": "run-0001",
                "text": "focus here",
            },
            {"session_id": SESSION_ID, "text": "focus here"},
        ),
        (
            {"commandType": "session.interrupt", "activeRunId": "run-0001"},
            {"session_id": SESSION_ID},
        ),
    ],
)
def test_execute_routes_only_three_supported_commands_with_fresh_params(
    command,
    expected_params,
):
    gateway = _RecordingGateway(_session_fixture())
    adapter = _adapter(gateway)

    receipt = adapter.execute(command, actor=_actor())

    assert receipt.accepted is True
    assert receipt.reason is None
    assert gateway.calls == [
        (command["commandType"], receipt.command_id, expected_params)
    ]


@pytest.mark.parametrize(
    "command",
    [
        {"method": "shell.exec", "params": {"command": "whoami"}},
        {"commandType": "shell.exec", "command": "whoami"},
        {
            "commandType": "prompt.submit",
            "text": "hello",
            "queueIfOffline": False,
            "method": "process.kill",
        },
        {
            "commandType": "approval.respond",
            "requestId": "request-0001",
            "choice": "always",
            "all": True,
        },
        {"commandType": "clarify.respond", "requestId": "request-0001", "answer": "A"},
        {"commandType": "session.create", "projectId": "project-1"},
        {"commandType": "interrupt.request", "activeRunId": "run-0001"},
        {
            "commandType": "session.interrupt",
            "activeRunId": "run-0001",
            "path": "C:/private",
        },
    ],
)
def test_execute_denies_generic_rpc_unadvertised_commands_and_smuggled_fields(command):
    gateway = _RecordingGateway(_session_fixture())
    adapter = _adapter(gateway)

    receipt = adapter.execute(command, actor=_actor())

    assert receipt.accepted is False
    assert receipt.reason == "method-unsupported"
    assert gateway.calls == []
    assert hasattr(adapter, "execute")
    assert not hasattr(adapter, "dispatch")
    assert not hasattr(adapter, "handle_request")


@pytest.mark.parametrize(
    ("actor_change", "command", "reason"),
    [
        (
            {"authenticated_session_id": "session-9999"},
            {"commandType": "prompt.submit", "text": "hello", "queueIfOffline": False},
            "session-mismatch",
        ),
        (
            {"session_revision": 6},
            {"commandType": "prompt.submit", "text": "hello", "queueIfOffline": False},
            "session-revision-mismatch",
        ),
        (
            {"capability_hash": "sha256-" + "B" * 43},
            {"commandType": "prompt.submit", "text": "hello", "queueIfOffline": False},
            "capability-stale",
        ),
        (
            {},
            {
                "commandType": "session.steer",
                "activeRunId": "run-other",
                "text": "hello",
            },
            "session-run-mismatch",
        ),
        (
            {},
            {"commandType": "session.interrupt", "activeRunId": "run-other"},
            "session-run-mismatch",
        ),
    ],
)
def test_execute_rejects_session_revision_capability_and_run_mismatches(
    actor_change,
    command,
    reason,
):
    gateway = _RecordingGateway(_session_fixture())
    adapter = _adapter(gateway)
    actor = replace(_actor(), **actor_change)

    receipt = adapter.execute(command, actor=actor)

    assert receipt.accepted is False
    assert receipt.reason == reason
    assert gateway.calls == []


def test_execute_sanitizes_gateway_failures_without_exception_or_gateway_text():
    gateway = _RecordingGateway(_session_fixture())
    gateway.response = {
        "jsonrpc": "2.0",
        "id": "remote-command",
        "error": {
            "code": 5000,
            "message": "Authorization: Bearer gateway-secret C:/private/path",
        },
    }
    adapter = _adapter(gateway)

    receipt = adapter.execute(
        {
            "commandType": "session.steer",
            "activeRunId": "run-0001",
            "text": "hello",
        },
        actor=_actor(),
    )

    assert receipt.accepted is False
    assert receipt.reason == "internal-unavailable"
    assert "gateway-secret" not in repr(receipt)
    assert "C:/private/path" not in repr(receipt)


def test_execute_rejects_offline_queueing_not_advertised_by_task_five():
    gateway = _RecordingGateway(_session_fixture())
    adapter = _adapter(gateway)

    receipt = adapter.execute(
        {"commandType": "prompt.submit", "text": "hello", "queueIfOffline": True},
        actor=_actor(),
    )

    assert receipt.accepted is False
    assert receipt.reason == "queue-disallowed"
    assert gateway.calls == []


def test_server_remote_command_seam_neutralizes_ambient_transport_and_is_fixed():
    with patch.dict(
        "sys.modules",
        {
            "hermes_constants": MagicMock(
                get_hermes_home=MagicMock(return_value="/tmp/hermes_test")
            ),
            "hermes_cli.env_loader": MagicMock(),
            "hermes_cli.banner": MagicMock(),
            "hermes_state": MagicMock(),
        },
    ):
        from tui_gateway import server

    invoke = getattr(server, "invoke_remote_session_command", None)
    assert invoke is not None, "adapter-safe remote command seam must exist"
    observed = []

    class AmbientTransport(Transport):
        def write(self, obj: dict) -> bool:
            del obj
            return True

        def close(self) -> None:
            pass

    ambient: Transport = AmbientTransport()
    original_handler = server._methods["prompt.submit"]
    original_transport = object()
    server._sessions[SESSION_ID] = {"transport": original_transport}
    token = server.bind_transport(ambient)

    def handler(rid, params):
        observed.append((rid, params, server.current_transport()))
        return server._ok(rid, {"status": "streaming"})

    server._methods["prompt.submit"] = handler
    try:
        response = invoke(
            "prompt.submit",
            "remote-command",
            {"session_id": SESSION_ID, "text": "hello"},
        )
        assert server._sessions[SESSION_ID]["transport"] is original_transport
    finally:
        server._methods["prompt.submit"] = original_handler
        server.reset_transport(token)
        server._sessions.pop(SESSION_ID, None)

    assert response["result"]["status"] == "streaming"
    assert observed == [
        (
            "remote-command",
            {"session_id": SESSION_ID, "text": "hello"},
            None,
        )
    ]
    with pytest.raises(ValueError):
        invoke("shell.exec", "remote-command", {"command": "whoami"})
