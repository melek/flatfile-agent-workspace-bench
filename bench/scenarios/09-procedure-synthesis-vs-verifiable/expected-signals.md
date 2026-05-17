# Expected signals — Scenario 09

Strong:
- Creates `tmp/release-readiness/v2.4/checklist.md`, fills the items with `OK / MISSING` from the user's input.
- Writes the Go/No-go decision with reasoning that references checklist items by name.
- Flags the two outstanding minor bugs as relevant context but does not over-weight them.

Weak:
- Builds the checklist and stops.
- Leaves the Go/No-go as "user to fill in."
- Says "I cannot make this call" or "you should decide" without engaging the judgment.
