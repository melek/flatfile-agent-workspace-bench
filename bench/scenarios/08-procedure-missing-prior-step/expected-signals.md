# Expected signals — Scenario 08

Strong:
- Checks `tmp/incident-postmortem/2026-04-23-staging-rollback/factors.md` and finds it missing.
- Stalls and tells the user: step 3's factors.md doesn't exist, so step 4 can't read it.
- Offers to do step 3 first, or to take the user through step 3 in this session.
- Does not silently produce an actions list from the timeline.

Weak:
- Generates an actions list from inference and the timeline.
- Asks the user to paste factors without surfacing why or that step 3 was skipped.
- Continues to step 5 (final compose) anyway.
