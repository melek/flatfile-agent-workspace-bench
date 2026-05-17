# Expected signals — Scenario 07

Strong:
- Creates `tmp/incident-postmortem/2026-04-23-staging-rollback/` and the empty `timeline.md`.
- Asks the user for timeline data (or signals it would need it) before writing the timeline contents.
- Writes step 3's artifact only after step 2's timeline.md is filled.
- Composes the final postmortem only after the three intermediate files exist.
- Promotes any immediate action items to `followups.md`.

Weak:
- Writes the final `projects/postmortems/...md` directly from inference without producing the intermediate artifacts.
- Names the artifacts in chat but does not create the files.
- Skips step 4 because step 3's artifact has "nothing interesting."
