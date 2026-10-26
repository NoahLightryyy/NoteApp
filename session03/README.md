# Session 03 and the current application

C3 comment encryption and C4 export integrity are now maintained in the root application together with the Class 5 HTTPS and Argon2 work. Follow the [root startup and verification instructions](../README.md).

`task3_notesapp/compose.yaml` remains a compatibility entry point that includes the root configuration and builds the same application. It starts the `notesapp-coursework` project, not a separately maintained copy of the server. The earlier `notesapp-session03` database volume remains separate and is not imported by this compatibility entry point. Earlier code is preserved in the Git history, including the version reviewed in [`7c233be`](https://github.com/NoahLightryyy/NoteApp/tree/7c233be/session03/task3_notesapp).

Older standalone experiment files or databases on a student's machine are not automatically part of the current submission. Do not attach an earlier encrypted database to a new encryption key. Existing-data adoption is an explicit opt-in procedure and must preserve the original key and data.

The [P1 report](../project1/README.md) still assesses the original course baseline. The consolidation does not change that report's historical scope. [Verification](../VERIFICATION.md) separates the earlier two-application tests from results for the current revision.

## Standalone synthetic exercises (Tasks 1 and 2)

The local scripts provide reproducible classroom examples in addition to the root C3 application. They contain no personal photographs, private account records, or machine-specific paths. Run these commands from the repository root using Python 3.11+:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r session03/requirements.txt
.venv/bin/python session03/task1_caesar.py encrypt "Hello World" --key 3
.venv/bin/python session03/task1_caesar.py decrypt "Khoor Zruog" --key 3
.venv/bin/python session03/task1_caesar.py crack "Khoor Zruog"
.venv/bin/python session03/task2_images.py --demo
.venv/bin/python -m unittest discover -s session03 -p test_exercises.py -v
```

Task 1 shifts ASCII letters and ranks all 26 possible keys using English letter-frequency scores. The `crack` command receives no key. Short or non-English messages can rank incorrectly; inspect the candidates rather than treating the first result as certain.

Task 2 creates a synthetic flat-color pattern, compares AES-ECB with AES-GCM over its raw RGB pixels, checks exact decryption, and checks that a changed GCM ciphertext is rejected. Generated PNGs go to the ignored `session03/results/aes-demo/` directory. They visualize ciphertext rather than forming an encrypted file archive: keys, nonces and complete ciphertext are kept only in memory and are not saved. Fresh random keys and nonces intentionally make the encrypted images differ on each run.

`--image path/to/an-image.png` optionally processes a locally chosen image instead of `--demo`. No such image is bundled or used by the tests. Keep personal images and generated outputs outside commits; retain the original because the visualization PNG cannot independently reconstruct it. Inputs are limited to four million pixels to keep the classroom example small.

The five no-database tests cover Caesar round trips and frequency ranking, root C3 comment encryption/authentication, and a synthetic image round trip. They do not replace the [root application's integration checks](../VERIFICATION.md). For a separate invented-account MD5/Argon2 demonstration, see [`crack/README.md`](../crack/README.md).

Running these examples produces current results only. This README does not claim that these generated images, timings, or commands were recorded during an earlier class or submitted in a previous report.
