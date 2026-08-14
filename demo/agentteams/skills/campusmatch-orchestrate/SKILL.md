---
name: campusmatch-orchestrate
description: Use when a user starts, resumes, or corrects a CampusMatch career evidence task.
assign_when: The Worker is the CampusMatch Team Leader coordinating the complete user workflow.
---

# Orchestrate CampusMatch

## Required sequence

1. Confirm mode, consent scope, material, and target JD.
2. Delegate profile extraction and JD parsing; they may run in parallel.
3. Run matching only after both structured outputs exist.
4. Run coaching only after matching.
5. Run Audit after every coaching revision.
6. Export only when Audit returns `PASS` and the human approves.

Use `mcporter call campusmatch.get_task_status task_id=<TASK_ID>` to inspect shared state. Retry the same idempotency key at most twice for a temporary tool failure. On missing input, ask one clear user question. On a contract error or repeated failure, stop and request human review.

## User-facing contract

Summarize: what was found, what evidence supports it, what remains uncertain, what the user should do next, and whether export is blocked. Never describe match score as hiring probability.
