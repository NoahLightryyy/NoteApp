# Project 1 requirements and submission check

Reviewed: **22 October 2026**. Submission owner: **Lv Songyuan — 2023901706**. Group membership clarified by the student on **26 October 2026**.

## Requirement source

The student's original uploaded slide was recovered and visually checked during this review: **Computer Security — Kristen Pire, Session 03, slide 31/32, “Project 1: threat model of NotesApp”**. It specifies groups of 3–4, 15% of the grade, four written deliverables, GitHub hand-in before 20 October, and a three-minute presentation per group on that day. The slide does not explicitly require Word, PDF, PowerPoint, attack demonstrations or implementation of every fix. This checklist does not infer additional requirements from later lab assignments.

## Written deliverables

| Slide requirement | Submitted evidence | Review result |
|---|---|---|
| Data-flow diagram with every trust boundary | [System overview](assets/system-overview.svg), [flow register](flows.md), role figures in the [report](README.md#group-role-diagrams) | Covers browsers, Flask, PostgreSQL, shell, container files/configuration, Docker/host access, direct DB access, spreadsheet interpretation and ping network traffic. TB1–TB7 and F01–F62 are identified. |
| STRIDE table, at least one threat per letter | [STRIDE table](README.md#stride-register-and-ratings), TH01–TH17 | All six categories represented; each entry has a scenario, scope, source evidence and mitigation. |
| Every threat rated by likelihood × impact | [Risk assessment](Risk_Assessment.md) | 17/17 scored, with defined 1–5 scales and separate likelihood/impact explanations. TH04 corrected to 4 × 4 = 16 to match its authenticated-account prerequisite. |
| Top three risks, each with a fix | [Top three](Top3_Risks_and_Fixes.md) | TH01 = 25, TH02 = 25, TH03 = 20; each has concrete changes and acceptance checks. First two are tied. |

The complete report in [README.md](README.md) governs the submission. The separate risk and Top 3 files are synchronized extracts retained for the student's requested group contribution. Group source files and sketches are supporting material; corrections and canonical numbering are documented in the complete report and flow register.

## Submission and group obligations

| Obligation | What is established | What is not established |
|---|---|---|
| GitHub hand-in | This fork received the P1 package in commit `68aad16` on 22 October 2026. | This does not establish an on-time submission before 20 October. An earlier group submission in another repository or an extension has not been verified. |
| Groups of 3–4 | The student confirmed three members: Lv Songyuan (2023901706), Liu Yunfei (2023905324), and Wu Siyuan (2023905932). There is no separate group repository; this fork is Lv Songyuan’s submission. | The other members’ own submissions or approval of this revision have not been established. |
| Three-minute group presentation | [English script](presentation.md) is included. | The student has deferred the presentation. A script is not evidence that it occurred, and no instructor exemption has been established. |

## Scope and evidence

The assessment is pinned to original commit `1c83e422429c4b784411701ffd797b5ab5f397dc`. Source references were checked against that commit, not today's modified application. Later fixes and lab tests are documented separately in the repository README. Scores are analytical judgments under an explicit network-accessible deployment assumption. Supporting observations are distinguished from source-supported findings and conditional threats; no unperformed exploit or load test is claimed.

AI assistance in organization, review, scoring suggestions and wording is disclosed in the main report. Group approval of the judgments and compliance with any additional teacher AI policy are not established by an automated file review.
