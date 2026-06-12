# RETIRED (2026-06-11)

**Designed to test:** the decision-vs-observation routing trap — when a user says
"we're going to use Postgres" (spoken intent, not a vetted commitment), does the agent
recognize it as not-yet-a-decision and hold the strict bar for `decisions.md`?

**Why it no longer measures the template:** this was the highest-tension scenario in
every benchmarked version (spread 2.60 / 2.30 / 2.05 across v0.1/v0.2/v0.3), and the
v0.3 summary's own inspection concluded the failure persists regardless of template
text: "the workspace's textual guidance has not been load-bearing for it. The mitigation
likely lives at the tool/plugin layer, not the text layer"
(`results/v0.3-trimmed/summary.md`, "Scenario 05 is the persistent failure mode").

A scenario whose outcome the artifact under test cannot move is measuring the agent and
harness, not the template — a task-validity failure per the Agentic Benchmark Checklist
(arXiv 2507.02825). Keeping it in the scored set adds a constant, template-insensitive
penalty to every version's architecture and safety means.

**Disposition:** retired from future aggregation. Frozen tags (`bench-frozen-v1`) and all
existing results retain it. The routing-trap behavior remains worth testing — but as an
evaluation of a routing *tool/plugin* (where the mitigation can actually live), not of
template prose.

See issue #2.
