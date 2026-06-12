# RETIRED (2026-06-11)

**Designed to test:** cold pickup against a stale forward-task tracker — does the agent
notice that a `followups.md` entry has gone stale across sessions and surface it rather
than acting on it blindly?

**Why it no longer measures that:** the v0.3 template trim removed forward-task tracking
(`followups.md`) from the documented workspace. The scenario seed still plants the file,
so v0.3+ agents encounter it as an *undocumented user-added file* — and the v0.3 summary
records exactly that drift: architecture −0.63 and safety −0.46 while cog-erg +0.45,
because agents used the file without the methodology framing the scenario assumed
(`results/v0.3-trimmed/summary.md`, "Scenario 03 is the design-cost scenario").

Per the task-validity criterion (Agentic Benchmark Checklist, arXiv 2507.02825), a
scenario should be passable iff the artifact under test provides the capability. Since
v0.3, this scenario measures behavior the template deliberately no longer prescribes.

**Disposition:** retired from future aggregation. Frozen tags (`bench-frozen-v1`) and all
existing results retain it — past comparisons are unaffected. A v0.3-native replacement
would test stale state via `projects/<name>/AGENTS.md` Status / Next-steps instead, under
a new scenario ID and a new frozen tag.

See issue #2.
