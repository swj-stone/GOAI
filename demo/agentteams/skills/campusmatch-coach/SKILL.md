---
name: campusmatch-coach
description: Use when an evidence match must become grounded resume, learning, and mock-interview guidance.
assign_when: The Worker is responsible for Coach Agent tasks in CampusMatch.
---

# Generate grounded coaching

After Match completes, call `campusmatch.generate_coaching` with `schema_version=1.0`, the assigned `task_id`, and a stable `idempotency_key`.

Every resume suggestion must carry evidence references. Preserve responsibility boundaries. Separate evidence-building actions from learning actions. Send the complete structured draft to Audit; never offer an unaudited draft as export-ready.
