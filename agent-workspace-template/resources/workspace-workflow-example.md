# A Day in This Workspace — Worked Example

A complete walk-through of one situation moving through each of the top-level files. Read this once to see how the workspace fits together. Safe to delete or replace with your own once you've internalized the pattern.

**A caution before reading:** this example is set in a B2B SaaS context (pricing strategy, customer deals). The *shape* of the workflow transfers to any domain — a journalist's investigation, a researcher's literature review, a household renovation. Don't let the example's flavor dictate your framing.

## The scenario

You run product at a SaaS company. This morning, leadership held an offsite. The team decided to move new customers from per-seat to usage-based pricing, effective 2026-07-01 — a real shift in how you go to market. Same day, four different files get touched.

## 1. `decisions.md` — the binding commitment

```markdown
## 2026-05-15 — Move to usage-based pricing for new customers

**Status:** accepted

**Context:** Per-seat pricing has been suppressing expansion. Procurement consistently stalled on seat counts — most recently with Acme Robotics, the third such deal this quarter (see `observations.md#2026-05-15-procurement-stalls-when-pricing-is-per-seat`). Leadership offsite this morning concluded the model has to change before scaling go-to-market further.

**Decision:** Effective 2026-07-01, all new customer contracts move to usage-based pricing keyed on events/month. Existing customers grandfathered for 12 months.

**Consequences:** Sales collateral and pricing page need rebuilds before 2026-07-01. We can no longer pitch per-seat to prospects after that date. The active Acme Robotics pitch becomes the first proof point for the new model.

**References:** `daybook/2026-05-15.md`, `observations.md#2026-05-15-procurement-stalls-when-pricing-is-per-seat`, `followups.md` (Acme Robotics — pricing-tier doc).
```

This is a **commitment that constrains future action**. A future reader asking "wait, are we still allowed to pitch per-seat?" finds the answer here. The ADR cites both the pattern that motivated it (an observation) and the specific deal it changes the shape of (a followup).

## 2. `observations.md` — the pattern that drove the decision

```markdown
## 2026-05-15 — Procurement stalls when pricing is per-seat

When sales cycles include a procurement step, the conversation gets stuck on "how many seats to buy" even after pitch and demo land well. Three deals over the last quarter showed this shape: Beacon Logistics (Feb), Northwind Foods (Apr), now Acme Robotics. Pattern, not a commitment.
```

This is **descriptive** — it names the recurring shape without binding future action. The observation existed across three deals before the decision was made; surfacing it as an entry lets the decision entry cite it instead of repeating it.

## 3. `followups.md` — the specific deal you're tracking

```markdown
- **2026-05-15 — Acme Robotics / pricing-tier doc** — expected by 2026-05-22. Sent the new usage-based pricing brief (see `decisions.md#2026-05-15-move-to-usage-based-pricing-for-new-customers`); they're sharing with their finance team. Chase Friday if no reply.
```

This is a **forward commitment**: you've handed something to someone and the loop is open. The entry will close when Acme responds (or you escalate). The ADR can reference it because the deal is now load-bearing for the new pricing model's first proof point.

## 4. `daybook/2026-05-15.md` — the chronological story

The day's narrative — Intent in the morning, Log accreted through the day, Handoff written before the EOD commit. See `daybook/0000-00-00-example.md` for the full filled version.

The key thing: the daybook is where the day's events happen *first*. The other three files get populated by promoting parts of the daybook (or the situation itself) into the right home.

## How the four interlock

| File | What it captures | Tense |
|---|---|---|
| `decisions.md` | Binding commitments | Future-binding |
| `observations.md` | Recurring patterns | Descriptive |
| `followups.md` | Outstanding asks | Forward-looking |
| `daybook/` | Today's events | Chronological |

Cross-references between them let a future reader (or a future agent) reconstruct what happened, why, and what's next, six months from now — without reading every daybook in order.

## Apply the shape to your own work

The same four-way routing works for any domain. A few translations:

- **Investigative reporting:** decision = editorial stance (e.g. "we name the source"); observation = pattern in interview subjects' framings; followup = waiting on a source's response; daybook = field notes and reporting log.
- **Literature review:** decision = inclusion criterion; observation = cross-paper theme; followup = waiting on a librarian's response; daybook = reading log.
- **Household administration:** decision = "we're switching insurance carriers"; observation = "the kitchen drain backs up after heavy rain"; followup = waiting on the plumber to call back; daybook = today's running list.

These files are domain-neutral. The Acme story is the easiest example to render coherent end-to-end, but the pattern doesn't belong to B2B.
