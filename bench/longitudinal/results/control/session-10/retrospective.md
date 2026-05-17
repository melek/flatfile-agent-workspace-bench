# Quarterly Retrospective: Verdant & Crestline (Last 5 Weeks)

## Executive Summary
Two parallel deployments, one on track and one correcting course mid-project. Both revealed a consistent pattern: **scope slippage driven by client discovery cycles, compounded by assumption gaps in data readiness.**

---

## Verdant Foods — Procurement Analytics Dashboard
**Status:** On track to delivery (Week 6, 2026-05-17)

### What Worked
- **Data extraction contract clarity.** Defining "raw extract" with Marcus upfront prevented weeks of rework. Early schema alignment with Ash eliminated ambiguity.
- **Milestone cadence.** Week 3 checkpoint (2026-04-14) caught training plan gaps before they blocked go-live.
- **Split ownership.** Separating data work (Ash) from training design (Priya) prevented bottlenecks.

### What Didn't
- **Plant POC lateness.** Marcus delayed providing plant representative list by 10 days. Training kickoff slipped 1 week; calendar coordination still incomplete.
- **Power user naming.** Assumed Priya could start curriculum design in Week 1; reality: can't design without knowing actual user skill levels across plants.

### Pattern to Name
**Discovery cycle underestimation.** We budgeted 2 weeks for data extraction but didn't account for the client's internal approval loops. Each plant needs sign-off on schema from local ops leads—a step not on the critical path until Week 2.

---

## Crestline Manufacturing (Scenario)
**Status:** Course correction in Week 3

### What Worked
- **Caught drift early.** Week 3 checkpoint revealed training materials were not aligned with dashboard UI. Rewrote in 5 days rather than post-deployment.
- **Client escalation clarity.** Clear escalation path to Marcus prevented blame loops when scope shifted.

### What Didn't
- **Scope creep not named.** Plant B requested "real-time inventory sync" in Week 2 (training was Week 4). We absorbed it as "fit it in" rather than renegotiating end-date.
- **Assumption: "standard" deployment.** Each plant operates differently. Deployed Plant A without asking—had to customize twice more.

### Pattern to Name
**Customization assumed away.** We priced 3 identical deployments. Reality: each plant has different purchasing workflows. This cost 2 weeks of rework and created training friction (power users learned the generic version, not their actual process).

---

## Recurring Shapes to Present to Board

1. **Client discovery > plan revision cycle is 1.5–2 weeks longer than estimated.**
   - Recommendation: Build 2-week discovery buffer into scope for multi-stakeholder projects.

2. **Assumption that deployments are "identical" fails when clients have distributed operations.**
   - Recommendation: Site visit or recorded ops-walk in Week 1 to capture plant-specific workflows before design.

3. **Power user training readiness depends on *actual* user roster, not templates.**
   - Recommendation: Lock user names and their current tool proficiency by end of Week 1.

---

## What I'd Do Differently
- Explicitly block data approval loops on the Gantt chart (client side, not our side—but still on the critical path).
- Add "plant workflow audit" as standalone Week 1 task; scope deployments after, not before.
- Require Marcus to confirm user roster before Priya starts curriculum design, not as a "nice to have."

---

## Next Quarter Outlook
If we address these three patterns, we can compress Verdant-like projects from 6 weeks to 5 and avoid Crestline's rework. The math is straightforward: remove discovery rework by front-loading discovery.
