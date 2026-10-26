# Coursework submission status

**Submission owner:** Lv Songyuan (2023901706). Initial review: **22 October 2026**. Delivery and group details clarified by the student on **26 October 2026**. This record distinguishes repository contents, reported delivery, and instructor acceptance.

## Requirements and evidence

The unified root revision passed 44 application regression tests and isolated deployment checks on 26 October; see [VERIFICATION.md](VERIFICATION.md) for exact source hashes and results. Five standalone exercise tests also passed. Earlier successful checks applied to the previous two-application layout. The default `notesapp-coursework` stack creates an independent database; older student databases have not been imported. The entries below identify the current review locations and distinguish them from the historical submissions.

| Item | Requirement source | Current review location | Delivery facts |
|---|---|---|---|
| P1 | Original Session 03 slide 31/32: diagram with trust boundaries; every STRIDE category; likelihood × impact per threat; Top 3 with fixes | [Original-baseline report](project1/README.md), diagrams, 17 scored threats and synchronized extracts | P1 materials uploaded to this fork; formal timing/presentation details are in the [P1 checklist](project1/SUBMISSION_CHECKLIST.md) |
| C3 | Original Session 03 slide 30: encrypt comments with AES-GCM; fresh nonce guidance on slide 32 | [Root application](web/app.py) and [verification record](VERIFICATION.md) | Previously uploaded as a separate lab; consolidated into the root application in this revision |
| C4 | Teacher’s class-5 audit column: HMAC-signed CSV export; the student’s explicit HMAC request | [Root application](web/app.py) and [verification record](VERIFICATION.md) | Previously uploaded as a separate lab; consolidated in this revision. The full original C4 rubric was not recovered for the earlier review |
| C5a / Lab 1 | [Official HTTPS lab](https://kristenpire.github.io/epita-security-labs/class5/https-lab/): findings sheet covering HTTP exposure, HTTPS recapture and certificate trust; working nginx HTTPS | Default [Compose configuration](docker-compose.yml), [nginx](nginx/nginx.conf), and [verification record](VERIFICATION.md) | Latest report privately sent to instructor, according to the student; implementation remains in GitHub |
| C5b / Lab 2 | [Official password audit](https://kristenpire.github.io/epita-security-labs/class5/password-audit/): wordlist attack, timing, held-out accounts, Argon2 comparison and verdict; legacy-login upgrade | [Root login](web/app.py), [hashing](web/password_security.py), and [verification record](VERIFICATION.md) | Latest report privately sent to instructor, according to the student; implementation and regression tests remain in GitHub |

The Class 5 hand-in is the findings sheet; implementation supports the experiment. On 26 October the student confirmed sending the latest Lab 1 / Lab 2 reports or ZIP, with both partners’ names and student IDs. These private reports are not republished here. Their receipt or grading by the instructor has not been independently verified.

## P1 membership

| Member | Student ID |
|---|---|
| Lv Songyuan | 2023901706 |
| Liu Yunfei | 2023905324 |
| Wu Siyuan | 2023905932 |

The student supplied these three members and confirmed that there is no separate group repository. This fork identifies Lv Songyuan as its submission owner; it does not establish that the other members have submitted or approved this revision. The Class 5 reports concern a different pair, Lv Songyuan and Zhang Fangyuchen, and are not attributed to the P1 group.

## Historical facts retained

- **Earlier deployment layout.** The 22 October submission used root `web/` for Class 5 login upgrades and a separate `session03/task3_notesapp` application for C3/C4. That separate copy bulk-migrated passwords at startup. The consolidation changes the current implementation, not the descriptions of earlier experiments.
- **Earlier tests.** The clean-copy results recorded with commit [`7c233be`](https://github.com/NoahLightryyy/NoteApp/commit/7c233be) are retained in [VERIFICATION.md](VERIFICATION.md#historical-verification--22-october-2026). Only a new run can verify the unified revision.
- **Alice’s migration history.** Earlier work had already migrated the live Alice account. Later successful logins were not her first plaintext-to-hash transition. The earlier supplemental test reenacted that transition in a transaction that was rolled back; it did not rewrite the historical experiment. The current compatibility test entry point uses fictional accounts in an isolated database, without modifying Alice.
- **SQL injection scaffold.** The Class 5 scaffold retained username SQL concatenation for a later class. This fork already used bound parameters and keeps that additional hardening; it does not reproduce the vulnerable scaffold exactly.
- **Report identity and version.** The reviewed private reports use “Lyu Songyuan” with the same student ID; the repository follows the student’s requested “Lv Songyuan”. The latest confirmed private submission includes both partners’ identification. The older bundle’s omitted partner/ID line does not describe that confirmed submission.
- **Historical prediction.** The Lab 2 report records the predicted time but says the predicted number of cracked accounts was not recorded. No prediction has been invented after the experiment.

The [P1 checklist](project1/SUBMISSION_CHECKLIST.md#submission-and-group-obligations) records the original deadline and the unresolved presentation status. Current implementation changes do not establish an earlier hand-in date or instructor exemption.
