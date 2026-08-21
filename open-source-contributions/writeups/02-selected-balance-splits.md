# 2. Fix selected balance counting unselected split children

- **Issue:** [actualbudget/actual#5525](https://github.com/actualbudget/actual/issues/5525)
- **Pull request:** [#8748](https://github.com/actualbudget/actual/pull/8748) — in review
- **Branch:** `fix-selected-balance-partial-splits`
- **Files changed:** 4 (+74 / −4)

## The bug

Shift+clicking a range of transactions in the account register shows a "Selected balance".
When the range included a **split transaction**, the total was wrong — the reporter saw
`72.39` where `59.51` was correct.

The bug only appears under one specific condition: the split is expanded and the selection
covers the parent plus **only some** of its children. If the whole split is selected, or the
split is collapsed, the total is correct — which is why it looked intermittent to maintainers.

## Root cause

`SelectedBalance` ran a query filtering on `id ∈ selected AND parent_id ∈ selected`, which
returns exactly the selected children whose parent is *also* selected. The old code then
removed those children from the id list and kept the parent. Because the sum query runs with
`options({ splits: 'all' })`, summing a parent sums **every** child of that split — including
children the user never selected.

## The fix

Drop the *parent* and keep the selected children instead. A parent selected on its own matches
no rows, so it is left untouched and still contributes the whole split.

## Verification

Two regression tests were added. Reverting only `Balance.tsx` to the pre-fix version and
re-running the suite fails with:

```
AssertionError: expected [ 'parent-1' ] to deeply equal [ 'child-1' ]
```

confirming the old code summed the parent. With the fix, all 6 tests pass.
