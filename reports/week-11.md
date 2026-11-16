# Semester Week 11 Progress Report — Initial LLM Integration

Student: Sofiya Serbina  
Course: CSS 4007 — Artificial Intelligence  
Project: Autonomous Agent for Reviewing and Repairing Hackathon Case Materials Before Publication  

## Completed Work

I implemented and tested the first LLM-powered prototype on the synthetic BondScope hackathon case. The prototype answers one organizer question: “What materials are available to participants, and what is each file for?”

I prepared five participant-facing files in `cases/bondscope/`: a case brief, a judging rubric, a data dictionary, a daily bond summary and a trade register. I placed the expected findings and corrected CSV in `evaluation/bondscope/` so they can be used later to assess the agent. The inventory tool only lists files from the participant directory.

I connected the Python application to the OpenAI API and registered `list_materials(case_id)` as a tool. The prototype reads its configuration from a local `.env` file. Basic installation and run instructions are included at the top of `src/bondscope.py`.

I completed two live runs. After the first run, I revised two file descriptions and repeated the same request to check whether the model would describe the data more accurately.

## Important Commits

| Date | Commit | Contribution |
| --- | --- | --- |
| 9 Nov 2026 | `d20e4c8` | Defined the agent’s scope, proposed tools and evaluation plan. |
| 9 Nov 2026 | `1409ec2` | Documented the Week 10 milestone and the next steps for Week 11. |
| 16 Nov 2026 | `afb83b4` | Updated the proposal to include evidence-backed CSV repairs and verification. |
| 16 Nov 2026 | `f85ac50` | Recorded the instructor’s feedback and the revised scope in the Week 10 addendum. |
| 16 Nov 2026 | `81aed45` | Added the synthetic BondScope case, expected repairs and review findings. |
| 17 Nov 2026 | `4ed222a` | Implemented the LLM-selected tool call for listing participant materials. |

## Current Functionality

The prototype supports two run modes:

- `python3 src/bondscope.py --list-only` runs the inventory tool locally and prints its result.
- `python3 src/bondscope.py` sends the organizer’s request to the model, executes the selected tool and returns its result to the model for the final answer.

The following exchange was observed in the second live run:

| Step | Observed result |
| --- | --- |
| Model | `gpt-4.1-mini` |
| User request | «Какие материалы доступны участникам кейса BondScope и для чего нужен каждый файл?» |
| Model-selected action | `list_materials({"case_id": "bondscope"})` |
| Tool result | `brief.md`, `daily_summary.csv`, `data_dictionary.md`, `rubric.md`, `trade_register.csv` |
| Final answer | The model listed all five files in Russian and explained their roles. It described `trade_register.csv` as a partial register of confirmed bond trades included in the case sample. |

The program validated the requested tool name and case ID before execution. It then passed the inventory back to the model and checked that the final answer included every returned filename. Both live runs listed all five participant files. Neither exposed the evaluation files.

## Problems Encountered

The first run returned the correct filenames, but the description of `trade_register.csv` suggested that it covered all relevant transactions. The tool had supplied only the generic role `trade register`. This distinction matters for BondScope because a transaction missing from a partial register does not establish that no trade occurred.

## Solutions

I changed the trade register’s role to `partial register of confirmed bond trades included in the case sample`. I also clarified that `daily_summary.csv` contains indicative prices and last trade prices where available.

I repeated the original request. This time the model explicitly described the trade register as a partial sample. Its final explanatory sentence still used the phrase «реальных торгов», although the case data is synthetic. I recorded this as a wording limitation for future evaluation.

## What I Learned

The live trace helped me distinguish the model’s action from the program’s action. The model requested `list_materials` and supplied the case ID. Python inspected the directory and returned the filenames and roles. The model then used that result to write its answer.

Comparing the two runs also showed why checking filenames alone is insufficient. Both answers named all five files, but only the second accurately conveyed the register’s limited coverage. Future tests should check whether a factual claim is supported as well as whether the expected files appear.

## Next Week

I will extend the prototype from listing materials to retrieving evidence from their contents. The first check will compare the spread requirement in `rubric.md` with the data promised for the MVP in `brief.md`. The expected output is a structured finding with a reference to each passage, an explanation of the issue and a question for the organizer.