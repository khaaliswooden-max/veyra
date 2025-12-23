# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for Veyra.

## What is an ADR?

An ADR is a document that captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this structure:

```markdown
# ADR-XXXX: Title

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-XXXX

## Context
What is the issue that we're seeing that is motivating this decision or change?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?
```

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-model-backend-abstraction.md) | Model Backend Abstraction | Accepted |
| [0002](0002-audit-trail-design.md) | Audit Trail Design | Accepted |

## Creating a New ADR

1. Copy `template.md` to `XXXX-title.md`
2. Fill in the sections
3. Update the index above
4. Submit a PR
