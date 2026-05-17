# Release Readiness Check

**When to run:** Before any production release.

**Inputs:**
- Staging test results
- Open bug list filtered to the release scope
- Release notes draft path
- Anything else the user surfaces

**Outputs:**
- `tmp/release-readiness/<release-id>/checklist.md` with the Go/No-go call recorded inline.

## Steps

1. **Build the checklist.** Create `tmp/release-readiness/<release-id>/checklist.md` using the template below. Fill in each item from the inputs the user provided. Flag missing items as `MISSING`, not `OK`. → produces `tmp/release-readiness/<release-id>/checklist.md`.

2. **Make the call.** Read the filled checklist from step 1. Under a new `## Go/No-go decision` header in the same file, write either `Go` or `No-go`, followed by 2–4 sentences of reasoning that reference the checklist items by name. This step has no programmatic test — the judgment is yours to make and the user's to verify. Do not punt to the user. → updates `tmp/release-readiness/<release-id>/checklist.md`.

## Template

```markdown
# Release Readiness — <release-id>

## Checklist

- [ ] Staging tests green
- [ ] No P0/P1 bugs open in release scope
- [ ] Release notes published
- [ ] On-call rotation aware
- [ ] Customer comms drafted (if applicable)

## Go/No-go decision

(written in step 2)
```
