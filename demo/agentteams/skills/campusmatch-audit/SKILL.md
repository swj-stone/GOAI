---
name: campusmatch-audit
description: Use when CampusMatch coaching or export must be checked for grounding, privacy, fairness, trace, consent, and approval.
assign_when: The Worker is responsible for Audit Agent tasks and final export gating in CampusMatch.
---

# Audit CampusMatch output

Call `mcp-campusmatch.audit_export` with the assigned `task_id`, a stable `idempotency_key`, and the actual consent, trace, and human-approval states.

Return every issue code and corrective action. `BLOCK` is final until the underlying content changes and a new audit runs. Never accept an unsupported number, expanded responsibility, sensitive-attribute score, missing trace, absent consent, or missing approval.
