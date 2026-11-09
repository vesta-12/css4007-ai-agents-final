# Project Proposal — Semester Week 10

Student: Sofiya Serbina  
Course: CSS 4007 — Artificial Intelligence  
Prepared on: 6 November 2026

## Project Title

Autonomous Agent for Reviewing Hackathon Cases Before Publication

## Problem Description

Before publishing a hackathon case, organizers need to establish whether participants can understand the required deliverables, access the necessary materials and receive a meaningful assessment under the judging criteria. Potential problems include contradictory requirements, references to missing attachments, undefined evaluation metrics and data that cannot support a required calculation.

The application will inspect the participant-facing brief, rubric and attachments together. It will identify evidence-supported discrepancies, explain their consequences and suggest focused questions or corrections. The organizer will use the report to decide what requires revision. The usefulness of these findings will be checked against annotated examples and, if available, feedback from an organizer.

## Target Users

- Hackathon organizers in technical communities such as GDG Narxoz.
- Partners and mentors who prepare challenge briefs, attachments and judging criteria.

Participant materials from the KASE and Decentraton cases are candidate examples. Their exact contents, completeness and permitted use will be checked before inclusion. Previously prepared participant solutions will be kept separate from the agent's review inputs to avoid giving the agent information participants did not receive.

## Selected Difficulty

A - Advanced.

A single LLM agent will pursue a review goal, select tools based on observations, maintain task state, adapt its plan and stop under explicit conditions. The implementation will satisfy the D/C foundations and the A-level autonomy, guardrail, traceability and evaluation requirements.

## Expected Functionality

The agreed first version will provide a local Streamlit web interface for uploading case materials, entering a review request and viewing findings, source references and the execution trace.

Supported review inputs will be text documents (TXT, Markdown and text-based PDF) and CSV attachments. The initial document workflow will check consistency between the brief, requested deliverables, available resources and judging criteria. PDF scans requiring OCR will be reported as unsupported input.

The CSV workflow will inspect column names, missing values, duplicate identifiers and key coverage between two tables. One predefined baseline will support a small binary classification case with explicit training and validation files, labels and an accuracy metric. It will learn the majority class from training labels and score its fixed predictions against validation labels. This checks that the supported evaluation path can run. It does not establish the general solvability of a case or the best achievable performance.

A missing CSV will be assessed against the requirements of the specific case. Product concept tasks can be complete without a dataset. Intentionally private final-test labels will be treated according to their stated role. Files absent from an incomplete archive will be described as unavailable in the reviewed copy.

Each finding will contain its type (confirmed discrepancy, clarification needed or suggested improvement), supporting evidence, practical consequence and proposed next action. A check that lacks evidence will remain unverified. The report will describe the checks completed and the review's coverage.

## Proposed Functions

| Function | Purpose | Inputs | Expected output | Dependencies |
| --- | --- | --- | --- | --- |
| `list_materials(case_id)` | Discover accessible materials and their declared roles | Validated case identifier | File IDs, file types, roles and availability | Case manifest and read-access policy |
| `find_evidence(case_id, file_ids, query)` | Retrieve passages supporting or qualifying a claim | Case ID, allowed document IDs and search terms | Excerpts with file and page/line references, or an explicit no-match result | Local text/PDF reader and search |
| `inspect_table(case_id, table_ids, key)` | Profile CSV data and, when requested, compare keys across tables | One or two allowed CSV IDs and an optional join key | Column and row summaries, missing-value counts, duplicate or unmatched keys | CSV processing and argument validation |
| `run_baseline(case_id, train_id, validation_id, target, metric)` | Exercise the supported prediction-and-scoring path | Allowed CSV IDs, binary target and `accuracy` | Training/validation counts, majority-class prediction and score, or a supported error | Fixed baseline implementation and validated data roles |
| `review_case(goal, case_id, limits)` | Coordinate model calls, state, validation and stopping | User request, case ID and configured budgets | Structured report, run status and trace | LLM adapter, tool dispatcher and output validator |

Python is the proposed implementation language. Streamlit will provide the interface, CSV processing will use pandas, and text-based PDF extraction will use a PDF reader such as pypdf. Exact package versions will be pinned when the environment is set up.

## Proposed Agent Tools

The first four functions will be registered as LLM-callable tools. The model will choose their arguments and sequence. A dispatcher will validate each request, execute the actual function and return its result to the model.

For example, after discovering that the brief refers to a second table, the agent can look for the attachment and inspect the relevant keys. If the table is missing, it can search the documentation for an alternative source and report a blocked check. If the necessary inputs are present, it can continue with the supported baseline. An explanation-only question may be answered without a tool call.

## Model Selection

The initial proposed model is GPT-4.1 mini through the OpenAI API, using function calling and a Python adapter. Access and a complete real-model tool-calling exchange will be verified during Week 11. The model identifier actually used will be documented with the results. A compatible model can be substituted if access or observed performance requires it, while preserving the agreed tool contracts and workflow.

API credentials will be supplied through environment variables. An example configuration and `.gitignore` will protect credentials. Deterministic mock responses will support repeatable unit and failure tests, alongside real-model demonstrations.

## Architecture

Streamlit will collect the user goal and materials, build a case manifest and start the agent. The agent will choose a tool, observe its validated result, update state and decide whether to continue, change its plan, request information or stop.

Explicit task state will contain the goal, available resources, evidence, completed checks, open questions, errors and remaining budgets. State will persist across steps in a run. The JSON trace will record the selected actions, validated arguments, tool outcomes, state changes and stopping reason. Observable actions and concise decision summaries will be logged without secrets or private reasoning.

The initial configurable limits will be 10 agent steps, 12 tool calls and one retry per failed operation. Retries count towards the overall budgets. Tool operations will also have appropriate size and time limits. Completion, a blocking information gap, unrecoverable failure and exhausted budgets will be explicit stopping conditions.

Permissions will be enforced in code. Tools will read only permitted files through validated case/file IDs. The baseline tool will execute predefined Python logic. Arbitrary commands and generated code will have no execution tool. Uploaded instructions will be treated as untrusted document content. External publishing and changes to original case files are outside the first version's read-only review workflow, so approval for external modifications does not apply.

Before returning success, the application will validate the report structure, ensure cited references correspond to retrieved evidence, check numerical claims against tool results and mark unresolved checks. The run status will distinguish completed, partial/needs-input and failed reviews. Evidence quality and whether a cited passage actually supports a finding will also be assessed in evaluation.

## Example Requests

1. Check whether the brief and judging rubric agree on what participants must submit. Cite any supported contradictions and draft questions for the author.
2. The brief refers to an attendance appendix. Locate it in the supplied materials and determine whether the required information is available. Explain which checks remain blocked.
3. Inspect the supplied training and validation CSV files and run the supported baseline if their roles, labels and metric are explicit. Report the measured score and any data issues.
4. Explain the purpose of a baseline in this review process.

## Evaluation Plan

Development will use a complete synthetic case and controlled variants with known defects. Candidate historical cases will provide additional examples if their materials are available and suitable. A separate case or previously unseen variant will be reserved for evaluation after development.

Expected findings and acceptable clarification questions will be annotated before runs. Record detected known defects, missed defects and false alarms. Review whether each source supports its finding, whether calculations match the tools and whether the agent stops appropriately. At least one real-model run will complete an end-to-end review, and contrasting cases will demonstrate decisions that change with intermediate observations. A fresh case variant will support the unseen-test defense.

At least 12 application tests will cover the following scenarios. Repository starter tests will be recorded separately.

| ID | Scenario and expected behavior |
| --- | --- |
| F1 | A consistent product case receives a supported review without an invented dataset requirement. |
| F2 | A known brief/rubric contradiction is reported with evidence from both sources. |
| F3 | A missing referenced appendix in a partial archive blocks the relevant check and produces a focused clarification. |
| F4 | Separate CSV tables produce correct key-coverage and missing-value results. |
| F5 | A complete synthetic classification case produces the expected baseline score using separate training and validation data. |
| F6 | An explanation-only request is answered appropriately without tools. |
| F7 | Parameterized malformed inputs, tool arguments and structured model outputs are rejected or recovered within the configured limits. |
| F8 | A transient model/API failure receives a bounded retry and truthful status reporting. |
| G1 | Prompt injection in uploaded content fails to trigger an unauthorized operation. |
| G2 | Repeated tool failure ends with a partial or failed status after bounded recovery. |
| G3 | A request to read a file outside the permitted case or access a private jury resource is blocked in code. |
| G4 | Reaching an execution limit stops further actions and records the reason and available partial results. |

An organizer's assessment of whether findings would improve a case will be sought if available. Such feedback will be reported separately from reproducible automated tests.

For the A-level research component, select a genuine LLM/agent paper first publicly released between 22 June and 22 December 2026, inclusive. Submit the title, authors, original release date, link and rationale in `reports/paper-selection.md` during Week 14. Prepare the required 5–7 minute presentation covering the method, experiments, results, limitations and at least one technical figure, algorithm or experiment.

## Weekly Milestones

| Semester week | Dates | Planned or recorded outcome |
| --- | --- | --- |
| 10 | 2–8 Nov | Proposal and planning deadlinе.|
| 11 | 9–15 Nov | Set up Python/API access and demonstrate the first real-model request. |
| 12 | 16–22 Nov | Implement document input, structured findings, source references, the initial Streamlit page and first application tests. Annotate synthetic cases. |
| 13 | 23–29 Nov | Implement and register the four tools, including CSV checks and the predefined baseline. Demonstrate real model-selected tool execution. |
| 14 | 30 Nov–6 Dec | Complete multi-step execution, explicit state, adaptive decisions and stopping conditions. Submit the eligible paper selection. |
| 15 | 7–13 Dec | Complete permission checks, input/argument validation, bounded recovery, execution limits and traces. Exercise the four mandatory guardrail scenarios. |
| 16 | 14–20 Dec | Run at least 12 application tests and separate real-model evaluation. Analyze errors, improve reliability, finalize interface/documentation and prepare the paper presentation. |
| 17 | 21–22 Dec | Complete `reports/final-report.md`, publish test results and AI-assistance disclosure, submit the fork URL and final commit hash, and demonstrate/defend the project. |

The final deadline is 22 December 2026, 23:59 UTC+05:00. Meaningful work and the corresponding `reports/week-11.md` through `reports/week-17.md` entries will be committed regularly using actual dates. Completed functionality, experiments and limitations will be reported as observed.
