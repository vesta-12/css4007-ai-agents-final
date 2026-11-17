# Semester Week 12 Progress Report — Core Functionality

Sofiya Serbina · CSS 4007 · ОТК.ai

## Completed Work

I built a review that answers one organizer question about the synthetic BondScope case. Can participants calculate the spread required by the judging rubric using the materials they receive? The review reads the rubric, brief and both CSV headers. It returns a structured finding with source lines, the impact on scoring and a next action.

I first demonstrated the review in Streamlit. In the subsequent ОТК.ai web interface, the organizer can open a cited line and read the participant files, including all 18 daily summary records and 17 trade records.

## Important Commits

| Commit | Contribution |
| --- | --- |
| `47eb6d4` | Implemented the spread review with references to participant materials. |
| `c7c8fa2` | Validated citation IDs and tested the review on modified and incomplete case packages. |
| `a323e0b` | Added the first interactive review in Streamlit. |
| `ad6dbd7` | Added the ОТК.ai review workspace, source navigation and full CSV previews. |

## Current Functionality

I ran the original case and two controlled variants with `gpt-4.1-mini`.

| Input | Final status | What the organizer learns |
| --- | --- | --- |
| Original BondScope package | `confirmed` | The rubric awards 20 points for the spread. Line 7 of `rubric.md` requires the best bid and ask at the same close. Line 13 of `brief.md` excludes those snapshots, and neither CSV header contains those fields. |
| Spread criterion removed | `no_issue` | The modified rubric does not require the spread. Missing bid and ask prices need no correction for this criterion. |
| Trade register unavailable | `incomplete` | The review identifies the missing file, marks input coverage as unknown and asks the organizer to supply the register. |

All seven unit tests passed. To reproduce the tests, run `python3 -m unittest discover -s tests -p 'test_evidence.py' -v`. With the local API key configured, run `python3 src/evidence.py --review` for the original case and `python3 scripts/check_spread_variants.py` for the variants. Launch the workspace with `python3 src/inbox_server.py`.

## Problems Encountered

In an early run the model correctly explained why the spread could not be calculated but assigned the status `no_issue`. Removing the criterion also exposed an invalid citation. With the register missing, one early response suggested generating prices.

## Solutions

The program derives the final status from the requirement, input sufficiency and source availability. It checks the model's citation IDs against retrieved lines and displays the original quotes. If a file is unavailable, the review requests that file. I repeated both variants after these changes.

## What I Learned

Changing one input file at a time helped me test the meaning of each status. Removing a requirement resolves this particular issue. Removing a source leaves an open question. A plausible explanation alone did not guarantee that the model assigned the right status.

## Next Week

I will start with `inspect_table` to compare bond IDs and dates across the two CSV files. The Week 13 plan also covers registering the five proposed tools, applying the two supported repair rules to a draft, verifying their results and implementing the predefined baseline.

One idea for later evaluation is to try one deliverable as a participant, then show which steps succeeded, which needed a repair and which still require the organizer. Suggestions inspired by public cases could be explored after the core repair workflow works.
