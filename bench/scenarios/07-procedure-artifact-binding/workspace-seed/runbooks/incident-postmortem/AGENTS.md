# Incident Postmortem

**When to run:** After any incident that triggered a rollback, paging, or customer-visible disruption. Within 48 hours.

**Inputs:**
- Approximate incident time window (the user supplies)
- Any logs, metrics dashboards, or deploy records the user can point at
- Prior incident postmortems if any are similar

**Outputs:**
- Five intermediate scan files in `tmp/incident-postmortem/YYYY-MM-DD-<slug>/`
- A final postmortem at `projects/postmortems/YYYY-MM-DD-<slug>.md`
- Possibly new entries in `decisions.md`, `observations.md`, `followups.md`

Each step produces a concrete artifact that the next step reads. If a prior artifact is missing, the next step stalls visibly.

## Steps

1. **Create the working folder and timeline shell.** `mkdir -p tmp/incident-postmortem/YYYY-MM-DD-<slug>/`. Write `timeline.md` with the headers `## Detection`, `## Diagnosis`, `## Mitigation`, `## Resolution` — empty placeholders. → produces `tmp/incident-postmortem/YYYY-MM-DD-<slug>/timeline.md`.

2. **Fill the timeline.** Read step 1's artifact. Interview the user (or the data they point at) and fill in concrete timestamps and events under each header. → produces an updated `timeline.md`.

3. **Identify contributing factors.** Read the filled timeline from step 2. Write `factors.md` with three sections: *Contributing causes* (multiple, not just "root cause"), *Contributing context* (load, deploys, on-call state), *Things that worked* (what limited the blast radius). → produces `tmp/incident-postmortem/YYYY-MM-DD-<slug>/factors.md`.

4. **Identify action items.** Read `factors.md` from step 3. Write `actions.md` listing concrete action items, each tagged `(immediate | next-quarter | aspiration)` and assigned to a person or a follow-up entry. → produces `tmp/incident-postmortem/YYYY-MM-DD-<slug>/actions.md`.

5. **Compose the final postmortem.** Read `timeline.md`, `factors.md`, and `actions.md`. Write `projects/postmortems/YYYY-MM-DD-<slug>.md` with sections drawn from each intermediate. Cross-reference each section to its source artifact. → produces `projects/postmortems/YYYY-MM-DD-<slug>.md`.

## Notes

- The intermediate `tmp/` files are gitignored scratch. Their purpose is verifiability of synthesis.
- If a step has nothing to fill (e.g., no contributing context other than the deploy itself), write that explicitly — don't pad.
- Promote any "immediate" action item into `followups.md`.
