# Project Proposal — Semester Week 10

Student: Sofiya Serbina  
Course: CSS 4007 — Artificial Intelligence  
Prepared on: 9 November 2026 (Asia/Almaty, UTC+05:00)  
Revised on: 16 November 2026, following instructor feedback  
Submission status: prepared after the Week 10 window of 2–8 November 2026.

## Project Title

Autonomous Agent for Reviewing and Repairing Hackathon Case Materials Before Publication

## Problem Description

Before publishing a hackathon case, organizers need to establish whether participants can understand the required deliverables, access the necessary materials and receive a meaningful assessment under the judging criteria. Potential problems include contradictory requirements, references to missing attachments, undefined evaluation metrics and data that cannot support a required calculation.

The application will inspect the participant-facing brief, rubric and attachments together. For each discrepancy, the agent will identify its source and decide whether the supplied materials establish a unique correction. Where a supported repair rule applies, it will make the change in a draft copy, check the result and show the organizer exactly what changed. If a fact is missing or two sources disagree, it will identify the affected requirement and ask a specific question. The usefulness of these findings will be checked against annotated examples and, if available, feedback from an organizer.

## Target Users

- Hackathon organizers in technical communities such as GDG Narxoz.
- Partners and mentors who prepare challenge briefs, attachments and judging criteria.

Participant materials from the KASE and Decentraton cases are candidate examples. Their exact contents, completeness and permitted use will be checked before inclusion. Previously prepared participant solutions will be kept separate from the agent's review inputs to avoid giving the agent information participants did not receive.

## Selected Difficulty

A — Advanced.

A single LLM agent will pursue a review goal, select tools based on observations, maintain task state, adapt its plan and stop under explicit conditions. The implementation will satisfy the D/C foundations and the A-level autonomy, guardrail, traceability and evaluation requirements.

## Expected Functionality

The agreed first version will provide a local Streamlit web interface for uploading case materials, entering a review request and viewing findings, source references and the execution trace. The organizer will be able to compare a corrected CSV with its source and approve the verified draft for export.

Supported review inputs will be text documents (TXT, Markdown and text-based PDF) and CSV attachments. The initial document workflow will check consistency between the brief, requested deliverables, available resources and judging criteria. PDF scans requiring OCR will be reported as unsupported input.

The CSV workflow will inspect column names, missing values, duplicate identifiers and key coverage between two tables. One predefined baseline will support a small binary classification case with explicit training and validation files, labels and an accuracy metric. It will learn the majority class from training labels and score its fixed predictions against validation labels. This checks that the supported evaluation path can run. It does not establish the general solvability of a case or the best achievable performance.

A missing CSV will be assessed against the requirements of the specific case. Product concept tasks can be complete without a dataset. Intentionally private final-test labels will be treated according to their stated role. Files absent from an incomplete archive will be described as unavailable in the reviewed copy.

Each finding will contain its type (confirmed discrepancy, clarification needed or suggested improvement), supporting evidence, practical consequence and proposed next action. A check that lacks evidence will remain unverified. The report will describe the checks completed and the review's coverage.

### Repair scope for the first version

| Finding | Agent action | Evidence and verification |
| --- | --- | --- |
| A join fails because an identifier has surrounding whitespace. | Trim the affected key in a draft CSV if the case defines spaces as insignificant. Preserve leading zeros and the original string type. | Cite the key definition. Check that trimming creates no duplicate keys, the intended row now matches exactly once and unrelated cells are unchanged. |
| A required cell is empty, but another supplied table contains the value. | Copy the value only when the case designates the second table as authoritative for that field and exactly one record matches the full declared key. | Record both cell locations. For attendance, match participant **and** event. Verify the copied value against the source and rerun the missing-value check. |
| No supplied source contains the value, multiple records match, or sources conflict. | Leave the cell as supplied. Identify the missing or conflicting evidence and ask the organizer for the source or decision needed. | Cite the materials inspected and record an unresolved finding. A blank attendance cell alone cannot establish absence. |
| Two documents disagree about a deliverable. | Quote both passages and draft a clarification question. If an authoritative instruction settles the issue, suggest replacement wording with a citation. | Show the relevant passages to the organizer. Document edits are suggestions in this version. |

Each proposed data change will identify the file, row key, column, before/after values and evidence. The report will distinguish verified draft repairs, suggestions and unresolved findings. The organizer can reject a draft after inspection.

## Proposed Functions

| Function | Purpose | Inputs | Expected output | Dependencies |
| --- | --- | --- | --- | --- |
| `list_materials(case_id)` | Discover accessible materials and their declared roles | Validated case identifier | File IDs, file types, roles and availability | Case manifest and read-access policy |
| `find_evidence(case_id, file_ids, query)` | Retrieve passages supporting or qualifying a claim | Case ID, allowed document IDs and search terms | Excerpts with file and page/line references, or an explicit no-match result | Local text/PDF reader and search |
| `inspect_table(case_id, table_ids, key)` | Profile CSV data and, when requested, compare keys across tables | One or two allowed CSV IDs and an optional join key | Column and row summaries, missing-value counts, duplicate or unmatched keys | CSV processing and argument validation |
| `run_baseline(case_id, train_id, validation_id, target, metric)` | Exercise the supported prediction-and-scoring path | Allowed CSV IDs, binary target and `accuracy` | Training/validation counts, majority-class prediction and score, or a supported error | Fixed baseline implementation and validated data roles |
| `repair_table(case_id, finding_id, rule)` | Apply one supported repair to a run-local copy | Current finding ID and one of the two repair rules | Draft ID, cell-level diff, evidence and verification results, or a reason the repair is blocked | Case-scoped draft storage, validated source roles, deterministic rule and post-repair checks |
| `review_case(goal, case_id, limits)` | Coordinate model calls, state, validation and stopping | User request, case ID and configured budgets | Structured report, run status and trace | LLM adapter, tool dispatcher and output validator |

Python is the proposed implementation language. Streamlit will provide the interface, CSV processing will use pandas, and text-based PDF extraction will use a PDF reader such as pypdf. Exact package versions will be pinned when the environment is set up.

## Proposed Agent Tools

The first five functions will be registered as LLM-callable tools. The model will choose their arguments and sequence. A dispatcher will validate each request, execute the actual function and return its result to the model.

For example, after discovering that the brief refers to a second table, the agent can look for the attachment and inspect the relevant keys. If a failed join meets the whitespace rule, it can call `repair_table`, inspect the verified result and continue reviewing the draft. If two keys would collapse to the same ID, the tool will return the ambiguity and the agent can request clarification. If the table is missing, it can search the documentation for an alternative source and report a blocked check. If the necessary inputs are present, it can continue with the supported baseline. An explanation-only question may be answered without a tool call.

## Model Selection

The initial proposed model is GPT-4.1 mini through the OpenAI API, using function calling and a Python adapter. Access and a complete real-model tool-calling exchange will be verified during Week 11. The model identifier actually used will be documented with the results. A compatible model can be substituted if access or observed performance requires it, while preserving the agreed tool contracts and workflow.

API credentials will be supplied through environment variables. An example configuration and `.gitignore` will protect credentials. Deterministic mock responses will support repeatable unit and failure tests, alongside real-model demonstrations.

## Architecture

Streamlit will collect the user goal and materials, build a case manifest and start the agent. The agent will choose a tool, observe its validated result, update state and decide whether to continue, change its plan, request information or stop.

Explicit task state will contain the goal, available resources, evidence, completed checks, open questions, errors, source and draft IDs, repair decisions, verification results, approval status and remaining budgets. State will persist across steps in a run. The JSON trace will record the selected actions, validated arguments, tool outcomes, state changes and stopping reason. Observable actions and concise decision summaries will be logged without secrets or private reasoning.

The initial configurable limits will be 10 agent steps, 12 tool calls and one retry per failed operation. Retries count towards the overall budgets. Tool operations will also have appropriate size and time limits. Completion, a blocking information gap, unrecoverable failure and exhausted budgets will be explicit stopping conditions.

Permissions will be enforced in code. Tools will access only permitted files through validated case/file IDs. The repair tool may write only to the current run’s draft area. The baseline tool will execute predefined Python logic. Arbitrary commands and generated code will have no execution tool. Uploaded instructions will be treated as untrusted document content. Original uploads remain immutable. Before showing a draft as exportable, the repair tool will rerun the affected check, compare the changed cells with the authorized edit and check for new key collisions or unintended changes. Failed checks block export. Export requires the organizer to approve the exact verified draft in Streamlit. A changed draft needs fresh approval. The runtime enforces this condition independently of the model, which has no approval or publishing tool.

Before returning success, the application will validate the report structure, ensure cited references correspond to retrieved evidence, check numerical claims against tool results and mark unresolved checks. The run status will distinguish completed, partial/needs-input and failed reviews. Evidence quality and whether a cited passage actually supports a finding will also be assessed in evaluation.

## Example Requests

1. Check whether the brief and judging rubric agree on what participants must submit. Cite any supported contradictions and draft questions for the author.
2. The brief refers to an attendance appendix. Locate it in the supplied materials and determine whether the required information is available. Explain which checks remain blocked.
3. Inspect the supplied training and validation CSV files and run the supported baseline if their roles, labels and metric are explicit. Report the measured score and any data issues.
4. Two rows have missing attendance values. Use the supplied event register to repair any row with an unambiguous source, then show me the diff and explain what remains unresolved.
5. Explain the purpose of a baseline in this review process.

## Evaluation Plan

Development will use a complete synthetic case and controlled variants with known defects. Candidate historical cases will provide additional examples if their materials are available and suitable. A separate case or previously unseen variant will be reserved for evaluation after development.

Expected findings and acceptable clarification questions will be annotated before runs. Annotate expected cell-level changes and cells that must stay untouched. Record detected known defects, missed defects, false alarms, correct repairs, missed repairs and unsupported edits. Compare each output CSV with its expected version and check that the original inputs are byte-for-byte unchanged. Review whether each source supports its finding, whether calculations match the tools and whether the agent stops appropriately. At least one real-model run will complete an end-to-end review, and contrasting cases will demonstrate decisions that change with intermediate observations. A fresh case variant will support the unseen-test defense.

At least 12 application tests will cover the following scenarios. Repository starter tests will be recorded separately.

| ID | Scenario and expected behavior |
| --- | --- |
| F1 | A consistent product case receives a supported review without an invented dataset requirement. |
| F2 | A known brief/rubric contradiction is reported with evidence from both sources. |
| F3 | A missing referenced appendix in a partial archive blocks the relevant check and produces a focused clarification. |
| F4 | Separate CSV tables produce correct key-coverage and missing-value results. |
| F5 | A complete synthetic classification case produces the expected baseline score using separate training and validation data. |
| F6 | An explanation-only request is answered appropriately without tools. |
| R1 | A permitted whitespace repair restores the intended join. The verified draft matches the expected CSV, including leading zeros. |
| R2 | Of two missing attendance values only one has an authoritative match for the same participant and event. Only that cell is filled. The report asks for evidence for the other. |
| R3 | A key collision or conflicting source values block the affected repair and produce a clarification request. |
| R4 | A failed post-repair check blocks export. Repeating a successful repair produces no additional changes. |
| F7 | Parameterized malformed inputs, tool arguments and structured model outputs are rejected or recovered within the configured limits. |
| F8 | A transient model/API failure receives a bounded retry and truthful status reporting. |
| G1 | Prompt injection in uploaded content fails to trigger an unauthorized operation. |
| G2 | Repeated tool failure ends with a partial or failed status after bounded recovery. |
| G3 | A request to read a file outside the permitted case or access a private jury resource is blocked in code. |
| G5 | An attempted export without organizer approval or with approval for an older draft is blocked. Approval of the exact verified draft permits export. Original uploads remain intact in each case. |
| G4 | Reaching an execution limit stops further actions and records the reason and available partial results. |

An organizer's assessment of whether findings would improve a case will be sought if available. Such feedback will be reported separately from reproducible automated tests.

For the A-level research component, select a genuine LLM/agent paper first publicly released between 22 June and 22 December 2026, inclusive. Submit the title, authors, original release date, link and rationale in `reports/paper-selection.md` during Week 14. Prepare the required 5–7 minute presentation covering the method, experiments, results, limitations and at least one technical figure, algorithm or experiment.

## Weekly Milestones

| Semester week | Dates | Planned or recorded outcome |
| --- | --- | --- |
| 10 | 2–8 Nov | Proposal and planning deadline was missed. The original proposal and retrospective report were prepared on 9 November in Week 11. The scope revision is dated 16 November. |
| 11 | 9–15 Nov | Upload the late proposal and report, confirm a usable sample case, set up Python/API access and demonstrate the first real-model request. |
| 12 | 16–22 Nov | Implement document input, structured findings, source references, the initial Streamlit page and first application tests. Record instructor feedback in the Week 10 addendum. Annotate synthetic cases with expected edits and intentional gaps. |
| 13 | 23–29 Nov | Implement and register the five tools, including the two CSV repair rules, their verification checks and the predefined baseline. Demonstrate real model-selected tool execution. |
| 14 | 30 Nov–6 Dec | Complete multi-step execution, explicit state, adaptive decisions, the draft comparison/approval flow and stopping conditions. Submit the eligible paper selection. |
| 15 | 7–13 Dec | Complete permission checks, input/argument validation, bounded recovery, execution limits and traces. Exercise the mandatory guardrail scenarios and verify draft-specific approval enforcement. |
| 16 | 14–20 Dec | Run at least 12 application tests and separate real-model evaluation. Analyze errors, improve reliability, finalize interface/documentation and prepare the paper presentation. |
| 17 | 21–22 Dec | Complete `reports/final-report.md`, publish test results and AI-assistance disclosure, submit the fork URL and final commit hash, and demonstrate/defend the project. |

The final deadline is 22 December 2026, 23:59 UTC+05:00. Meaningful work and the corresponding `reports/week-11.md` through `reports/week-17.md` entries will be committed regularly using actual dates. Completed functionality, experiments and limitations will be reported as observed.