# ADR-0002: Audit Trail Design

## Status
Accepted

## Date
2024-12-03

## Context

Veyra operates in high-stakes environments (defense, infrastructure, healthcare) where:

1. **Complete auditability** is a regulatory and operational requirement
2. **Tamper evidence** is critical—logs must detect modification
3. **Privacy preservation** matters—we can't log raw prompts containing sensitive data
4. **Performance** cannot be significantly impacted by logging
5. **Offline operation** must be supported (interplanetary scenarios)

Existing logging solutions (ELK, CloudWatch, etc.) don't provide tamper evidence and require network connectivity.

## Decision

We will implement a **Hash-Chained Audit Trail** with the following design:

### 1. Audit Entry Structure

```python
@dataclass
class AuditEntry:
    event_id: str           # Unique identifier
    event_type: AuditEventType  # execution, safety_check, etc.
    timestamp: datetime     # UTC timestamp
    actor: str              # Who/what performed action
    action: str             # What was done
    resource: str           # What was affected
    outcome: str            # success/failure/blocked
    input_summary: str      # Hash or summary (NOT raw input)
    output_summary: str     # Length or hash (NOT raw output)
    previous_hash: str      # Link to previous entry
    entry_hash: str         # Hash of this entry
    metadata: dict          # Additional context
```

### 2. Hash Chain Integrity

Each entry's hash is computed from:
```python
hash_data = {
    "event_id": entry.event_id,
    "event_type": entry.event_type.value,
    "timestamp": entry.timestamp.isoformat(),
    "actor": entry.actor,
    "action": entry.action,
    "outcome": entry.outcome,
    "previous_hash": entry.previous_hash,
}
entry_hash = sha256(json.dumps(hash_data, sort_keys=True))
```

This creates a blockchain-like structure where any modification breaks the chain.

### 3. Storage Backends

- **In-memory**: Default for testing, short-lived processes
- **SQLite**: Default for persistent, single-node operation
- **PostgreSQL**: Future option for distributed deployment

### 4. Privacy Preservation

- Raw prompts → SHA-256 hash (first 12 chars)
- Raw outputs → Length only
- Sensitive metadata → Redacted or hashed

### 5. Verification

```python
def verify_integrity(self) -> tuple[bool, Optional[str]]:
    """Verify hash chain integrity."""
    for i, entry in enumerate(entries):
        if entry.previous_hash != expected_prev:
            return False, f"Chain broken at {i}"
        if entry.entry_hash != compute_hash(entry):
            return False, f"Hash mismatch at {i}"
    return True, None
```

## Consequences

### Positive
- Tamper-evident logging detects any modification
- Works offline without network connectivity
- Privacy-preserving (no raw sensitive data logged)
- SQLite provides zero-config persistence
- Verification can be done anytime

### Negative
- Cannot search by prompt content (only hashes)
- Hash chain must be maintained strictly in order
- Concurrent writes require serialization
- Chain verification is O(n)

### Neutral
- Storage grows linearly with operations
- Old entries can be archived but chain must be preserved
- Different storage backends have different trade-offs

## Alternatives Considered

1. **Traditional logging (append-only files)**: No tamper evidence
2. **External blockchain**: Overkill, network dependency
3. **Merkle trees**: More complex, better for parallel verification (deferred)
4. **Write-ahead log**: No tamper evidence without additional measures

## Implementation Notes

- Entry hash uses SHA-256 truncated to 16 chars (64 bits) for readability
- Timestamps always UTC to avoid timezone issues
- Verification should run on startup and periodically

## References
- `src/veyra/governance/audit.py` - Implementation
- `src/veyra/nano.py` - SQLite-backed implementation
- NIST SP 800-92 - Guide to Computer Security Log Management
