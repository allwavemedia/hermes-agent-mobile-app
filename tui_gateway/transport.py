"""Transport abstraction for the tui_gateway JSON-RPC server.

Historically the gateway wrote every JSON frame directly to real stdout.  This
module decouples the I/O sink from the handler logic so the same dispatcher
can be driven over stdio (``tui_gateway.entry``) or WebSocket
(``tui_gateway.ws``) without duplicating code.

A :class:`Transport` is anything that can accept a JSON-serialisable dict and
forward it to its peer.  The active transport for the current request is
tracked in a :class:`contextvars.ContextVar` so handlers — including those
dispatched onto the worker pool — route their writes to the right peer.

Backward compatibility
----------------------
``tui_gateway.server.write_json`` still works without any transport bound.
When nothing is on the contextvar and no session-level transport is found,
it falls back to the module-level :class:`StdioTransport`, which wraps the
original ``_real_stdout`` + ``_stdout_lock`` pair.  Tests that monkey-patch
``server._real_stdout`` continue to work because the stdio transport resolves
the stream lazily through a callback.
"""

from __future__ import annotations

import copy
import contextvars
import errno
import json
import logging
import os
import queue
import threading
from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional, Protocol, runtime_checkable

# Errno values that mean "the peer is gone" rather than "the host has a
# real I/O problem".  Anything outside this set re-raises so it surfaces
# in the crash log instead of looking like a clean disconnect.
_PEER_GONE_ERRNOS = frozenset({
    errno.EPIPE,        # write to closed pipe (POSIX)
    errno.ECONNRESET,   # peer reset the connection
    errno.EBADF,        # fd closed under us
    errno.ESHUTDOWN,    # transport endpoint shut down
    getattr(errno, "WSAECONNRESET", -1),  # win32 mapping (no-op on POSIX)
    getattr(errno, "WSAESHUTDOWN", -1),
} - {-1})

logger = logging.getLogger(__name__)

# Optional knob: when true, StdioTransport does not call ``stream.flush``
# after writing.  Use this on environments where a half-closed pipe (TUI
# Node parent quit while the gateway is still emitting events) makes
# flush block long enough to starve the rest of the worker pool.
#
# IMPORTANT: Python text stdout is fully buffered when attached to a
# pipe (the TUI case), so this knob ONLY makes sense when the gateway
# is launched with ``-u`` or ``PYTHONUNBUFFERED=1``.  Without one of
# those, JSON-RPC frames will accumulate in the buffer and the TUI
# will hang waiting for ``gateway.ready``.  Default stays off so the
# existing flush-after-write behaviour is unchanged.
_DISABLE_FLUSH = (os.environ.get("HERMES_TUI_GATEWAY_NO_FLUSH", "") or "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


@runtime_checkable
class Transport(Protocol):
    """Minimal interface every transport implements."""

    def write(self, obj: dict) -> bool:
        """Emit one JSON frame. Return ``False`` when the peer is gone."""

    def close(self) -> None:
        """Release any resources owned by this transport."""


_current_transport: contextvars.ContextVar[Optional[Transport]] = (
    contextvars.ContextVar(
        "hermes_gateway_transport",
        default=None,
    )
)


def current_transport() -> Optional[Transport]:
    """Return the transport bound for the current request, if any."""
    return _current_transport.get()


def bind_transport(transport: Optional[Transport]):
    """Bind *transport* for the current context. Returns a token for :func:`reset_transport`."""
    return _current_transport.set(transport)


def reset_transport(token) -> None:
    """Restore the transport binding captured by :func:`bind_transport`."""
    _current_transport.reset(token)


@dataclass(frozen=True)
class SessionEventDelivery:
    """One isolated listener delivery or an explicit replay-reset signal."""

    kind: Literal["event", "reset-required"]
    session_id: str
    frame: dict | None = None
    reason: str | None = None


_LISTENER_STOP = None


class SessionEventSubscription:
    """Bounded asynchronous delivery for one session listener."""

    __slots__ = (
        "_closed",
        "_hub",
        "_lock",
        "_queue",
        "_reset_required",
        "_session_id",
        "_sink",
        "_subscriber_id",
        "_thread",
    )

    def __init__(
        self,
        hub: "SessionEventHub",
        session_id: str,
        subscriber_id: str,
        sink: Callable[[SessionEventDelivery], None],
        max_queue: int,
    ) -> None:
        self._hub = hub
        self._session_id = session_id
        self._subscriber_id = subscriber_id
        self._sink = sink
        self._queue: queue.Queue[SessionEventDelivery | None] = queue.Queue(
            maxsize=max_queue
        )
        self._lock = threading.Lock()
        self._closed = False
        self._reset_required = False
        self._thread = threading.Thread(
            target=self._run,
            name=f"hermes-session-listener-{subscriber_id}",
            daemon=True,
        )
        self._thread.start()

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def subscriber_id(self) -> str:
        return self._subscriber_id

    def enqueue(self, frame: dict) -> None:
        """Queue a copied event without waiting for listener work."""

        with self._lock:
            if self._closed or self._reset_required:
                return

            delivery = SessionEventDelivery(
                kind="event",
                session_id=self._session_id,
                frame=copy.deepcopy(frame),
            )
            try:
                self._queue.put_nowait(delivery)
                return
            except queue.Full:
                self._reset_required = True

            while True:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

            self._queue.put_nowait(
                SessionEventDelivery(
                    kind="reset-required",
                    session_id=self._session_id,
                    reason="queue-overflow",
                )
            )

    def _finish_from_worker(self) -> None:
        with self._lock:
            self._closed = True
        self._hub._drop(self)

    def _run(self) -> None:
        while True:
            delivery = self._queue.get()
            if delivery is _LISTENER_STOP:
                return

            try:
                self._sink(delivery)
            except Exception:
                logger.debug(
                    "session listener failed session=%s subscriber=%s",
                    self._session_id,
                    self._subscriber_id,
                    exc_info=True,
                )
                self._finish_from_worker()
                return

            if delivery.kind == "reset-required":
                self._finish_from_worker()
                return

    def close(self) -> None:
        """Stop future delivery without waiting on a blocked listener."""

        with self._lock:
            if self._closed:
                return
            self._closed = True

            while True:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
            self._queue.put_nowait(_LISTENER_STOP)

        self._hub._drop(self)


class SessionEventHub:
    """Thread-safe registry of bounded, nonblocking session listeners."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._order_locks: dict[str, threading.Lock] = {}
        self._subscriptions: dict[
            tuple[str, str], SessionEventSubscription
        ] = {}

    def subscribe(
        self,
        session_id: str,
        subscriber_id: str,
        sink: Callable[[SessionEventDelivery], None],
        *,
        max_queue: int = 256,
    ) -> SessionEventSubscription:
        if not session_id or not subscriber_id:
            raise ValueError("session_id and subscriber_id are required")
        if max_queue < 1:
            raise ValueError("max_queue must be at least one")

        key = (session_id, subscriber_id)
        with self._lock:
            if key in self._subscriptions:
                raise ValueError("subscriber is already registered for this session")
            self._order_locks.setdefault(session_id, threading.Lock())
            subscription = SessionEventSubscription(
                self,
                session_id,
                subscriber_id,
                sink,
                max_queue,
            )
            self._subscriptions[key] = subscription
        return subscription

    def publish(self, session_id: str, frame: dict) -> None:
        """Enqueue independent frame copies; never call listener code inline."""

        with self._lock:
            subscriptions = [
                subscription
                for (subscribed_session, _), subscription in self._subscriptions.items()
                if subscribed_session == session_id
            ]

        for subscription in subscriptions:
            subscription.enqueue(frame)

    def write_then_publish(
        self,
        session_id: str,
        frame: dict,
        write: Callable[[], bool],
    ) -> bool:
        """Preserve the local write order when concurrent emitters race."""

        with self._lock:
            order_lock = self._order_locks.get(session_id)

        if order_lock is None:
            return write()

        with order_lock:
            written = write()
            self.publish(session_id, frame)
            return written

    def _drop(self, subscription: SessionEventSubscription) -> None:
        key = (subscription.session_id, subscription.subscriber_id)
        with self._lock:
            if self._subscriptions.get(key) is subscription:
                del self._subscriptions[key]

    def close(self) -> None:
        with self._lock:
            subscriptions = list(self._subscriptions.values())
        for subscription in subscriptions:
            subscription.close()
        with self._lock:
            self._order_locks.clear()


class StdioTransport:
    """Writes JSON frames to a stream (usually ``sys.stdout``).

    The stream is resolved via a callable so runtime monkey-patches of the
    underlying stream continue to work — this preserves the behaviour the
    existing test suite relies on (``monkeypatch.setattr(server, "_real_stdout", ...)``).
    """

    __slots__ = ("_stream_getter", "_lock")

    def __init__(self, stream_getter: Callable[[], Any], lock: threading.Lock) -> None:
        self._stream_getter = stream_getter
        self._lock = lock

    def write(self, obj: dict) -> bool:
        """Return ``True`` on success, ``False`` ONLY when the peer is gone.

        Returning ``False`` is the dispatcher's "broken stdout pipe" signal
        — ``entry.py`` calls ``sys.exit(0)`` when ``write_json`` reports
        ``False``.  So programming errors (non-JSON-safe payloads, encoding
        misconfig, unexpected ValueErrors, host I/O bugs like ENOSPC) MUST
        NOT return ``False``, otherwise a real bug looks like a clean
        disconnect and is harder to diagnose.  Those re-raise so the
        existing crash-log infrastructure records the traceback.

        Peer-gone branches:
          * ``BrokenPipeError``
          * ``ValueError("...closed file...")``
          * ``OSError`` whose errno is in :data:`_PEER_GONE_ERRNOS`
            (EPIPE / ECONNRESET / EBADF / ESHUTDOWN; plus WSA mappings
            on Windows).  Other OSError errnos (ENOSPC, EACCES, ...) are
            real host problems and re-raise.
        """
        # Serialization is OUTSIDE the lock so a large payload can't
        # block other threads emitting their own frames.  A non-JSON-safe
        # payload is a programming error: re-raise so the crash log
        # captures it instead of silently exiting via the False path.
        line = json.dumps(obj, ensure_ascii=False) + "\n"

        with self._lock:
            stream = self._stream_getter()
            try:
                stream.write(line)
            except BrokenPipeError:
                return False
            except ValueError as e:
                # ValueError("I/O operation on closed file") is the
                # ONLY ValueError that means "peer gone".  Anything
                # else — including UnicodeEncodeError, which is a
                # ValueError subclass for misconfigured locales —
                # is a real bug; re-raise so it surfaces in the crash log.
                if isinstance(e, UnicodeEncodeError) or "closed file" not in str(e):
                    raise
                return False
            except OSError as e:
                if e.errno not in _PEER_GONE_ERRNOS:
                    raise
                logger.debug("StdioTransport write peer gone: %s", e)
                return False

            # A flush that *raises* with a peer-gone errno means the
            # dispatcher should exit cleanly.  A flush that *hangs* on
            # a half-closed pipe holds the lock until it returns — see
            # ``_DISABLE_FLUSH`` for the "skip flush entirely" escape
            # hatch.
            if not _DISABLE_FLUSH:
                try:
                    stream.flush()
                except BrokenPipeError:
                    return False
                except ValueError as e:
                    if isinstance(e, UnicodeEncodeError) or "closed file" not in str(e):
                        raise
                    return False
                except OSError as e:
                    if e.errno not in _PEER_GONE_ERRNOS:
                        raise
                    logger.debug("StdioTransport flush peer gone: %s", e)
                    return False

        return True

    def close(self) -> None:
        return None


class TeeTransport:
    """Mirrors writes to one primary plus N best-effort secondaries.

    The primary's return value (and exceptions) determine the result —
    secondaries swallow failures so a wedged sidecar never stalls the
    main IO path.  Used by the PTY child so every dispatcher emit lands
    on stdio (Ink) AND on a back-WS feeding the dashboard sidebar.
    """

    __slots__ = ("_primary", "_secondaries")

    def __init__(self, primary: "Transport", *secondaries: "Transport") -> None:
        self._primary = primary
        self._secondaries = secondaries

    def write(self, obj: dict) -> bool:
        # Primary first so a slow sidecar (WS publisher) never delays Ink/stdio.
        ok = self._primary.write(obj)
        for sec in self._secondaries:
            try:
                sec.write(obj)
            except Exception:
                pass
        return ok

    def close(self) -> None:
        try:
            self._primary.close()
        finally:
            for sec in self._secondaries:
                try:
                    sec.close()
                except Exception:
                    pass
