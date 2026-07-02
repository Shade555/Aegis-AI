"""In-memory manager for execution sessions."""

import asyncio
from typing import AsyncGenerator, Optional
from uuid import UUID

from aegis.application.execution.models import ExecutionEvent, ExecutionSession


class SessionManager:
    """A simple in-memory registry holding active execution sessions.

    This fulfills the MVP requirement to allow the API to query observable execution status.
    """

    def __init__(self) -> None:
        self._sessions: dict[UUID, ExecutionSession] = {}
        self._subscribers: dict[UUID, list[asyncio.Queue[ExecutionEvent]]] = {}

    def register_session(self, session: ExecutionSession) -> None:
        """Stores a session in memory."""
        self._sessions[session.audit_id] = session
        self._subscribers[session.audit_id] = []

    def get_session(self, audit_id: UUID) -> Optional[ExecutionSession]:
        """Retrieves a session by its audit_id."""
        return self._sessions.get(audit_id)

    async def subscribe(self, audit_id: UUID) -> AsyncGenerator[ExecutionEvent, None]:
        """Subscribe to a stream of events for a specific session."""
        session = self.get_session(audit_id)
        if not session:
            return

        queue: asyncio.Queue[ExecutionEvent] = asyncio.Queue()
        if audit_id not in self._subscribers:
            self._subscribers[audit_id] = []
        self._subscribers[audit_id].append(queue)

        try:
            while True:
                event = await queue.get()
                yield event
                # Close the stream on terminal events
                if event.event_type in (
                    "ExecutionCompleted",
                    "ExecutionFailed",
                    "AgentEventType.COMPLETE",
                    "AgentEventType.ERROR",
                ):
                    # We only close the stream on overall Execution completion, not individual agent complete.
                    # Wait, the stream should close on execution completion, which is handled in engine.py.
                    pass
        except asyncio.CancelledError:
            pass
        finally:
            if audit_id in self._subscribers and queue in self._subscribers[audit_id]:
                self._subscribers[audit_id].remove(queue)

    def broadcast_event(self, audit_id: UUID, event: ExecutionEvent) -> None:
        """Broadcast an event to all active subscribers of the session."""
        if audit_id in self._subscribers:
            for queue in self._subscribers[audit_id]:
                queue.put_nowait(event)

    def remove_session(self, audit_id: UUID) -> None:
        """Removes a session from memory."""
        if audit_id in self._sessions:
            del self._sessions[audit_id]
        if audit_id in self._subscribers:
            del self._subscribers[audit_id]

    def clear(self) -> None:
        """Clears all sessions (mostly for testing)."""
        self._sessions.clear()
        self._subscribers.clear()


# Singleton instance for the MVP
session_manager = SessionManager()
