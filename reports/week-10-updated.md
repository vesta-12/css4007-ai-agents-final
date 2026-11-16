# Semester Week 10 Progress Report — Scope Update

Student: Sofiya Serbina  
Course: CSS 4007 — Artificial Intelligence  
Original reporting window: 2–8 November 2026  
Update prepared: 16 November 2026 (semester Week 12)

This addendum records a revision to the [Week 10 proposal](proposal.md) following instructor feedback. The [original Week 10 report](week-10.md), prepared on 9 November, records the missed deadline. This entry documents the planning work completed on 16 November.

## Instructor Feedback

The instructor asked for the agent to resolve issues it can establish from the case materials. A useful review should give the organizer a corrected artifact when the evidence determines the fix. Where evidence is missing or contradictory, the organizer needs to know exactly what input or decision is required.

## Changes to the Proposal

- Extended the workflow from finding a discrepancy to locating its source, applying a supported fix to a draft CSV and verifying the result.
- Defined two initial repairs: trimming surrounding whitespace in identifiers when the case permits it, and filling a missing field from an authoritative table using a unique match on the full key.
- Added a fifth model-callable tool, `repair_table`. Its deterministic rules will check source authority, reject ambiguity and record the before/after values and supporting evidence.
- Added a source/draft comparison and organizer approval of the exact verified version before export. Conflicting document instructions will produce cited passages and a clarification question.
- Extended the evaluation plan with expected output CSVs and tests for correct repairs, ambiguous matches, failed verification and unauthorized export.

## Planned Demonstration

A synthetic case has two blank attendance cells. The event register confirms one participant’s attendance at the specified event. The agent should copy that value into the draft and cite the source row. For the second participant, the register contains only an entry for a different event. The agent should leave that cell blank and ask for the record for the relevant event. The organizer should see exactly one changed cell before approving the draft for export.

## Current Status and Next Step

The deliverables for this update are the revised proposal and this addendum. The repair tool, interface and tests are planned work. The next step is to prepare the synthetic input tables and expected output, then use them to check that a supported repair changes only the intended cell. Implementation results and commit references belong in the report for the week in which the work takes place.
