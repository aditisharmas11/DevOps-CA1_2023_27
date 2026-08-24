# 3. Don't send a starting balance of 0 when only the starting date is set

- **Issue:** [actualbudget/actual#8105](https://github.com/actualbudget/actual/issues/8105)
- **Pull request:** [#8750](https://github.com/actualbudget/actual/pull/8750) — in review
- **Branch:** `fix-banksync-custom-start-date`
- **Files changed:** 3 (+101 / −23)

## The bug

When linking an account to bank sync with a custom starting **date** but no explicit starting
**balance**, a balance of `0` was sent instead of no balance at all — so the account opened
with an incorrect starting figure.

## The fix

Distinguish "no starting balance provided" from "a starting balance of zero", and only send
the balance when the user actually set one.
