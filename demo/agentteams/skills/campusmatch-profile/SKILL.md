---
name: campusmatch-profile
description: Use when authorized resume, course, club, volunteer, or self-confirmed material must become an evidence-linked profile.
assign_when: The Worker is responsible for Profile Agent tasks in CampusMatch.
---

# Build an evidence-linked profile

Call `mcporter list mcp-campusmatch --schema` if the tool contract is not already known. Then call `mcp-campusmatch.profile_materials` with the assigned `task_id`, a stable `idempotency_key`, `user_id`, `source_id`, and the complete Markdown material.

Accept a capability only when the response includes a valid `evidence_ref`, verbatim quote, source ID, and line coordinates. Return `NEEDS_INPUT` if material is empty or unreadable. Do not infer missing facts. Report the artifact and task ID to the Team Leader.
