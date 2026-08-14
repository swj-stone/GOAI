---
name: campusmatch-match
description: Use when a confirmed profile and parsed job must be compared with evidence-backed scoring.
assign_when: The Worker is responsible for Match Agent tasks in CampusMatch.
---

# Calculate evidence match

After Profile and Job stages complete, call `campusmatch.match_evidence` with `schema_version=1.0`, the assigned `task_id`, and a stable `idempotency_key`.

Use the returned score; never calculate or alter it in prose. Present every requirement state and its evidence. Explain that `NO_EVIDENCE` is not proof of inability, `POLICY_EXCLUDED` is not counted, and match score is not hiring probability. On `TASK_INPUTS_MISSING`, tell the Team Leader which prerequisite must run.
