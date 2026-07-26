"""Contract tests for isolated, bounded remote session event listeners."""

import importlib
import threading
import time
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


def _transport_module() -> ModuleType:
    return importlib.import_module("tui_gateway.transport")


def _hub_type():
    hub_type = getattr(_transport_module(), "SessionEventHub", None)
    assert hub_type is not None, "the bounded session event hub must exist"
    return hub_type


@pytest.fixture()
def server():
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
        module = importlib.import_module("tui_gateway.server")
        yield module
        module._sessions.clear()
        module._pending.clear()
        module._answers.clear()
        module._live_transports.clear()


class _RecordingTransport:
    def __init__(self, order: list[str]) -> None:
        self.frames: list[dict] = []
        self.order = order

    def write(self, frame: dict) -> bool:
        self.frames.append(frame)
        self.order.append(f"local:{frame['params']['payload']['index']}")
        return True

    def close(self) -> None:
        pass


def _frame(session_id: str, index: int) -> dict:
    return {
        "jsonrpc": "2.0",
        "method": "event",
        "params": {
            "type": "message.delta",
            "session_id": session_id,
            "payload": {"index": index},
        },
    }


def test_server_preserves_local_transport_identity_order_and_async_delivery(server):
    subscribe = getattr(server, "subscribe_session_events", None)
    assert subscribe is not None, "server listener registration must exist"

    order: list[str] = []
    delivered = []
    listener_entered = threading.Event()
    release_listener = threading.Event()
    write_finished = threading.Event()
    primary = _RecordingTransport(order)
    server._sessions["session-1"] = {"transport": primary}

    def slow_sink(delivery) -> None:
        order.append(f"remote:{delivery.frame['params']['payload']['index']}")
        delivered.append(delivery)
        listener_entered.set()
        release_listener.wait(timeout=2)

    subscription = subscribe(
        "session-1",
        "mobile-1",
        slow_sink,
        max_queue=4,
    )
    first = _frame("session-1", 1)

    writer = threading.Thread(
        target=lambda: (
            server.write_json(first),
            write_finished.set(),
        )
    )
    writer.start()

    try:
        assert write_finished.wait(timeout=1), "listener work blocked the agent path"
        assert listener_entered.wait(timeout=1)
    finally:
        release_listener.set()
        writer.join(timeout=1)
        subscription.close()

    assert server._sessions["session-1"]["transport"] is primary
    assert primary.frames == [first]
    assert primary.frames[0] is first
    assert delivered[0].frame == first
    assert delivered[0].frame is not first
    assert order == ["local:1", "remote:1"]


def test_two_subscribers_receive_independent_copies_in_exact_order():
    hub = _hub_type()()
    received_a = []
    received_b = []
    done_a = threading.Event()
    done_b = threading.Event()

    def sink_a(delivery) -> None:
        delivery.frame["params"]["payload"]["consumer"] = "a"
        received_a.append(delivery.frame["params"]["payload"]["index"])
        if len(received_a) == 3:
            done_a.set()

    def sink_b(delivery) -> None:
        assert "consumer" not in delivery.frame["params"]["payload"]
        received_b.append(delivery.frame["params"]["payload"]["index"])
        if len(received_b) == 3:
            done_b.set()

    first = hub.subscribe("session-2", "mobile-a", sink_a, max_queue=4)
    second = hub.subscribe("session-2", "mobile-b", sink_b, max_queue=4)

    try:
        for index in range(1, 4):
            hub.publish("session-2", _frame("session-2", index))

        assert done_a.wait(timeout=1)
        assert done_b.wait(timeout=1)
    finally:
        first.close()
        second.close()
        hub.close()

    assert received_a == [1, 2, 3]
    assert received_b == [1, 2, 3]


def test_concurrent_writers_preserve_the_local_session_event_order(server):
    subscribe = getattr(server, "subscribe_session_events", None)
    assert subscribe is not None, "server listener registration must exist"

    first_write_entered = threading.Event()
    release_first_write = threading.Event()
    remote_done = threading.Event()
    local_order = []
    remote_order = []

    class _InterleavingTransport:
        def write(self, frame: dict) -> bool:
            index = frame["params"]["payload"]["index"]
            local_order.append(index)
            if index == 1:
                first_write_entered.set()
                release_first_write.wait(timeout=2)
            return True

        def close(self) -> None:
            pass

    def sink(delivery) -> None:
        remote_order.append(delivery.frame["params"]["payload"]["index"])
        if len(remote_order) == 2:
            remote_done.set()

    primary = _InterleavingTransport()
    server._sessions["session-ordered"] = {"transport": primary}
    subscription = subscribe(
        "session-ordered",
        "mobile-order",
        sink,
        max_queue=4,
    )
    first = threading.Thread(
        target=server.write_json,
        args=(_frame("session-ordered", 1),),
    )
    second = threading.Thread(
        target=server.write_json,
        args=(_frame("session-ordered", 2),),
    )

    try:
        first.start()
        assert first_write_entered.wait(timeout=1)
        second.start()
        time.sleep(0.05)
        release_first_write.set()
        first.join(timeout=1)
        second.join(timeout=1)
        assert remote_done.wait(timeout=1)
    finally:
        release_first_write.set()
        subscription.close()

    assert local_order == [1, 2]
    assert remote_order == local_order


def test_subscriber_exception_isolated_from_other_subscribers():
    hub = _hub_type()()
    failed = threading.Event()
    healthy_frames = []
    healthy_done = threading.Event()

    def broken_sink(_delivery) -> None:
        failed.set()
        raise RuntimeError("subscriber failed")

    def healthy_sink(delivery) -> None:
        healthy_frames.append(delivery.frame["params"]["payload"]["index"])
        if len(healthy_frames) == 2:
            healthy_done.set()

    broken = hub.subscribe("session-3", "broken", broken_sink, max_queue=4)
    healthy = hub.subscribe("session-3", "healthy", healthy_sink, max_queue=4)

    try:
        hub.publish("session-3", _frame("session-3", 1))
        assert failed.wait(timeout=1)
        hub.publish("session-3", _frame("session-3", 2))
        assert healthy_done.wait(timeout=1)
    finally:
        broken.close()
        healthy.close()
        hub.close()

    assert healthy_frames == [1, 2]


def test_queue_overflow_drops_pending_events_and_emits_one_reset_signal():
    hub = _hub_type()()
    entered = threading.Event()
    release = threading.Event()
    reset_received = threading.Event()
    deliveries = []

    def slow_sink(delivery) -> None:
        deliveries.append(delivery)
        if delivery.kind == "event":
            entered.set()
            release.wait(timeout=2)
        else:
            reset_received.set()

    subscription = hub.subscribe(
        "session-4",
        "slow-mobile",
        slow_sink,
        max_queue=1,
    )

    try:
        hub.publish("session-4", _frame("session-4", 1))
        assert entered.wait(timeout=1)
        hub.publish("session-4", _frame("session-4", 2))
        hub.publish("session-4", _frame("session-4", 3))
        hub.publish("session-4", _frame("session-4", 4))
        release.set()
        assert reset_received.wait(timeout=1)
    finally:
        release.set()
        subscription.close()
        hub.close()

    assert [delivery.kind for delivery in deliveries] == [
        "event",
        "reset-required",
    ]
    assert deliveries[0].frame["params"]["payload"]["index"] == 1
    assert deliveries[1].frame is None
    assert deliveries[1].reason == "queue-overflow"
