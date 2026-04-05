"""
Audit Trail System

Provides complete, tamper-evident audit logging for all Veyra operations.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class AuditEventType(Enum):
    """Types of auditable events."""

    EXECUTION = "execution"
    TOOL_INVOCATION = "tool_invocation"
    POLICY_CHECK = "policy_check"
    SAFETY_CHECK = "safety_check"
    CONFIGURATION_CHANGE = "configuration_change"
    ERROR = "error"
    SYSTEM = "system"


@dataclass
class AuditEntry:
    """A single audit log entry."""

    event_type: AuditEventType
    timestamp: datetime
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Actor information
    actor: str = "system"
    actor_type: str = "internal"

    # Event details
    action: str = ""
    resource: str = ""
    outcome: str = "success"

    # Data
    input_summary: str | None = None
    output_summary: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Chain integrity
    previous_hash: str | None = None
    entry_hash: str | None = None

    def compute_hash(self) -> str:
        """Compute hash of this entry."""
        data = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "outcome": self.outcome,
            "previous_hash": self.previous_hash,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "actor_type": self.actor_type,
            "action": self.action,
            "resource": self.resource,
            "outcome": self.outcome,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "metadata": self.metadata,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }


class AuditTrail:
    """
    Maintains a tamper-evident audit trail.

    Uses hash chaining to detect any modifications to historical records.
    """

    def __init__(self, persist_path: Path | None = None):
        """
        Initialize audit trail.

        Args:
            persist_path: Optional path to persist audit log
        """
        self._entries: list[AuditEntry] = []
        self._persist_path = persist_path
        self._last_hash: str | None = None

    def record(
        self,
        event_type: AuditEventType,
        action: str,
        resource: str = "",
        outcome: str = "success",
        actor: str = "system",
        input_summary: str | None = None,
        output_summary: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """
        Record an audit event.

        Args:
            event_type: Type of event
            action: Action performed
            resource: Resource affected
            outcome: Outcome (success, failure, etc.)
            actor: Actor performing the action
            input_summary: Summary of input (not full data for privacy)
            output_summary: Summary of output
            metadata: Additional metadata

        Returns:
            The created audit entry
        """
        entry = AuditEntry(
            event_type=event_type,
            timestamp=datetime.now(UTC),
            actor=actor,
            action=action,
            resource=resource,
            outcome=outcome,
            input_summary=input_summary,
            output_summary=output_summary,
            metadata=metadata or {},
            previous_hash=self._last_hash,
        )

        # Compute and store hash
        entry.entry_hash = entry.compute_hash()
        self._last_hash = entry.entry_hash

        self._entries.append(entry)

        # Persist if configured
        if self._persist_path:
            self._append_to_file(entry)

        return entry

    def _append_to_file(self, entry: AuditEntry) -> None:
        """Append entry to persistent storage."""
        if self._persist_path is None:
            return
        with open(self._persist_path, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def verify_integrity(self) -> tuple[bool, str | None]:
        """
        Verify the integrity of the audit chain.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self._entries:
            return True, None

        previous_hash = None
        for i, entry in enumerate(self._entries):
            # Check previous hash linkage
            if entry.previous_hash != previous_hash:
                return False, f"Hash chain broken at entry {i}"

            # Verify entry hash
            computed_hash = entry.compute_hash()
            if entry.entry_hash != computed_hash:
                return False, f"Entry {i} hash mismatch"

            previous_hash = entry.entry_hash

        return True, None

    def get_entries(
        self,
        event_type: AuditEventType | None = None,
        actor: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """
        Query audit entries.

        Args:
            event_type: Filter by event type
            actor: Filter by actor
            since: Filter by timestamp
            limit: Maximum entries to return

        Returns:
            List of matching entries
        """
        entries = self._entries

        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        if actor:
            entries = [e for e in entries if e.actor == actor]
        if since:
            entries = [e for e in entries if e.timestamp >= since]

        return entries[-limit:]

    def export(self, path: Path) -> None:
        """Export full audit trail to file."""
        with open(path, "w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)

    def __len__(self) -> int:
        return len(self._entries)
