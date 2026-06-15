# Observations

Append-only log of findings that **cost significant inference to arrive at** and would help future-you (or the agent) avoid re-deriving them. The optional second log alongside `decisions.md`.

**The bar is utility-shaped.** Ask: *would future-me (or the agent) waste time deriving this again?* If yes, save it. If no, leave it in the daybook Log or let it pass. Expect sparse use; quality over quantity.

What earns an entry:

- A non-obvious gotcha that already cost you time once and would cost it again. ("In repo X, paths under `/wp-content/` are runtime URLs, not source paths — `git ls-tree` before any vendor write.")
- A domain rule that constrains decisions but isn't itself a commitment we made. ("Company policy: Teams 365 only; no Google services.")
- A framing pattern that future-you would re-discover. ("Stakeholder X frames status updates by product narrative, not by feature — phrase Linear titles accordingly.")
- A pointer to longer reference material. Long items live in `resources/`; `observations.md` carries the pointer + the rule.

What does *not* belong: in-progress thoughts (daybook Log), commitments that constrain future action (`decisions.md`), one-off findings unlikely to recur.

**Without `observations.md`:** the same gotchas keep costing the same time. The agent re-derives the same rule on every relevant session. Findings that would save inference next time get lost in the daybook chronology.

## Template

```markdown
## YYYY-MM-DD — Short title

The finding, in one or two short sentences. If there's a rule, name it explicitly ("Rule: …"). If there's a longer reference, link to it under `resources/`.
```

## Shape

> ## 2026-05-15 — Wolf-related project delays follow a pattern
>
> Three completed builds have been damaged or destroyed by wolf activity this year: the straw house (2026-02, total loss), the stick house (2026-03, partial structural failure), the May site (pending insurance review). All three sat on routes the local pack uses seasonally. Rule: any new build on a wolf-frequented route adds a 2-week structural buffer and a brick-tier materials quote; verify route status against the pack's seasonal pattern before quoting.

If an observation crystallizes into a commitment, write the commitment in `decisions.md` and reference this observation in its Context.

---

<!-- Add your observations below. Newest at the bottom. -->
