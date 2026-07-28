---
name: loop-audit
description: Run an audit round that ships no features — find the strongest claim a repository makes about itself, build an independent probe, and measure whether it still holds. Use when several rounds have passed with everything green, when drift is suspected, or when asked to audit, stress-test, or verify a claim.
when_to_use: The loop has been green for several consecutive rounds, or a documented claim has never been measured. Trigger phrases include "audit this", "does that claim still hold", "stress-test the benchmark", "verify what the README says". Ships no features by design.
argument-hint: [optional claim to audit]
---

# Audit round

Run **§A Audit round** of the protocol below. Ship no features. The deliverable is
a measurement.

If a claim is named here, audit that one: $ARGUMENTS

Otherwise select the target yourself using the ordering in §A.

Do not fix what you find in this round — the fix is a separate round with its own
before/after number.

---

!`cat "${CLAUDE_PLUGIN_ROOT}/LOOP.md"`
