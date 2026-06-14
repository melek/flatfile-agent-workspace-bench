# Weekly Review

**When to run:** End of each working week — typically Friday afternoon. Move it to Monday morning if Friday gets eaten; missing a week occasionally is fine, missing four in a row means the ritual is dying.

**Inputs:**
- This week's `daybook/YYYY-MM-DD.md` files
- `followups.md` (current state)
- This week's entries in `decisions.md` and `observations.md`
- `projects/*/AGENTS.md` (skim each Status section)

**Outputs:**
- Four intermediate scan files in `tmp/weekly-review/YYYY-WW/` (one per input stream)
- A final review at `projects/weekly-review/YYYY-WW.md` (composed from the scans, using `template.md`)
- Possibly new entries in `followups.md`, `decisions.md`, `observations.md`, or `projects/*/AGENTS.md`

Each step produces a concrete artifact that the next step reads. If a step's artifact isn't on disk, the next step has nothing to consume and the review stalls visibly rather than drifting through synthesis-by-vibes.

## Steps

1. **Create the working folder.** `mkdir -p tmp/weekly-review/YYYY-WW/` (use the ISO week number from `date +%G-W%V` on Linux/macOS). → produces `tmp/weekly-review/YYYY-WW/` on disk.

2. **Summarize this week's daybooks.** Read each `daybook/YYYY-MM-DD.md` from this week in chronological order. Write `tmp/weekly-review/YYYY-WW/daybook-summary.md` with four sections: *Wins* (concrete things that landed), *Misses* (things that didn't land, with why), *Notable patterns* (things that came up more than once), *Open threads* (work mid-flight crossing the week boundary). → produces `tmp/weekly-review/YYYY-WW/daybook-summary.md`.

3. **Scan followups.** Read `followups.md`. Write `tmp/weekly-review/YYYY-WW/followups-scan.md` listing: *Overdue* (expected-by date passed), *Due soon* (next 7 days), *Quiet too long* (active but no movement in 2+ weeks), *Recently closed* (last 7 days). → produces `tmp/weekly-review/YYYY-WW/followups-scan.md`.

4. **Scan this week's decisions and observations.** Read entries in `decisions.md` and `observations.md` dated within this week. Write `tmp/weekly-review/YYYY-WW/records-scan.md` listing: *New decisions this week* (one line each, link to anchor), *New observations* (same), *Supersession candidates* (older decision entries that this week's work has contradicted or made obsolete). → produces `tmp/weekly-review/YYYY-WW/records-scan.md`.

5. **Scan projects.** Read the Status section of each `projects/*/AGENTS.md`. Write `tmp/weekly-review/YYYY-WW/projects-scan.md` listing each project with: *What moved* (changes since last review, or initial state if new), *What's stale* (no meaningful update in 2+ weeks), *Status changes* (e.g. `active` → `blocked`). → produces `tmp/weekly-review/YYYY-WW/projects-scan.md`.

6. **Compose the final review.** `cp runbooks/weekly-review/template.md projects/weekly-review/YYYY-WW.md`. Fill it in by reading the four scan files from steps 2–5. Be honest in Misses — soft language defeats the point. → produces `projects/weekly-review/YYYY-WW.md`.

7. **Force disagreement.** Pick one decision or observation from this week's outputs that the agent itself contributed (drafted, suggested, or framed). Articulate a credible counter-position grounded in this week's actual artifacts — not a generic "on the other hand," but a specific reading of the evidence that points the other way. Add it as a `## Counter-position considered` section to the final review. If no credible counter exists, write one sentence explaining why (and ground that explanation in the artifacts too — don't rationalize). → produces an updated `projects/weekly-review/YYYY-WW.md`.

8. **Promote action items back into the live files.** Any "I need to do X next week" becomes a `followups.md` entry or shows up in next week's daybook Intent. Any pattern that crystallized into a commitment becomes a `decisions.md` entry. Any pattern that's still descriptive but worth keeping → `observations.md`. → produces edits to `followups.md`, possibly `decisions.md` and `observations.md`.

9. **Commit.** Meaningful waypoint; the commit message should name the week. `git add . && git commit -m "weekly-review: YYYY-WW"`.

## Notes

- The four intermediate scan files in `tmp/` are gitignored scratch by design. They exist to keep the synthesis verifiable: each one is a small, focused artifact you (or the user) can audit before the final composition.
- The review *uses* the daybook and the top-level files as input but doesn't replace them — it's a synthesis layer.
- Step 7 (Force disagreement) is not a ritual flourish. The agent that drafted half of this week's records will, by default, ratify them in synthesis. The counter-position section is the small piece of friction that breaks the loop — see the Leveson-style risk note in `runbooks/AGENTS.md#performative-confirmation`.
- If a week was fully reactive and produced no synthesizable signal, write a one-line entry that says so in `projects/weekly-review/YYYY-WW.md` and move on. Skip the scan files for that week. Don't perform the ritual for its own sake.
- Read past weekly reviews when prepping for monthly or quarterly retros — they're the natural input.
