---
name: campusmatch-job
description: Use when a job description must be classified for job search, career change, or role exploration.
assign_when: The Worker is responsible for Job Agent tasks in CampusMatch.
---

# Parse a job description

Call `campusmatch.parse_job` with `schema_version=1.0`, the assigned `task_id`, a stable `idempotency_key`, `job_id`, `mode`, and complete JD Markdown.

Verify that scoring requirements total 100, ambiguous descriptions have behavior questions, and policy risks have weight 0. Never evaluate the user. If no supported requirement is found, return `NEEDS_INPUT`. Send structured results and risk items to the Team Leader.
