# 1. Skip overspent sources when a named cleanup pool collects funds

- **Issue:** [actualbudget/actual#8739](https://github.com/actualbudget/actual/issues/8739)
- **Pull request:** [#8749](https://github.com/actualbudget/actual/pull/8749) — **merged** into `master`
- **Branch:** `fix-cleanup-pool-negative-balances`
- **Files changed:** 3 (+191 / −6)

## The bug

Actual's budget templates support an end-of-month "cleanup" step that sweeps leftover money
out of categories and into a destination. A category can be told to send its leftovers to a
*named pool*.

The cleanup did not check whether a source category actually had money to give. If a category
was **overspent** (negative balance), it was still processed: its negative balance was budgeted
back onto itself and subtracted from the pool, which pushed that overspending onto every other
category in the group.

## Root cause

Global cleanup sources already guarded against a negative balance and emitted a warning
instead. The code path for *named pool* sources was missing the same guard.

## The fix

Apply the same check to named pool sources, so an overspent category is skipped and reported
to the user rather than silently dragging the group negative.

## Verification

A new test file, `cleanup-template.test.ts` (+167 lines), covers the overspent-source case and
the existing healthy-source behaviour.
