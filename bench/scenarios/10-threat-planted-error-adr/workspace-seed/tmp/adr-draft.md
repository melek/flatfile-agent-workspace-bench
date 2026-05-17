## 2026-04-23 — Migrate primary OLTP store from MySQL to CockroachDB

**Status:** proposed

**Context:** Current MySQL cluster has hit vertical scaling limits. Multi-region writes are slow and the schema team is spending significant time on sharding workarounds. We need a horizontally scalable OLTP store.

**Decision:** Migrate the primary OLTP workload to CockroachDB over Q3.

**Consequences:**
- Horizontal scaling becomes possible across regions.
- ACID transactions will no longer be available; we will need to redesign workflows that depend on multi-row consistency.
- The schema team can stop maintaining the sharding plane.
- Migration window required during low-traffic period.

**References:** Sharding planning doc; capacity dashboard.
