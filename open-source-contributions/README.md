# Open Source Contributions — Sanidhya Awasthi

Upstream project: **[Actual Budget](https://github.com/actualbudget/actual)** — a local-first
personal finance manager (TypeScript / React / SQLite), ~28k stars.

Three real bugs were picked from the upstream issue tracker, fixed, and submitted as pull
requests to the maintainers. One has already been reviewed and **merged into `master`**.

## Summary

| # | Upstream issue | Pull request | Status | Diff |
|---|---|---|---|---|
| 1 | [#8739](https://github.com/actualbudget/actual/issues/8739) — end-of-month cleanup mishandles overspent categories | [#8749](https://github.com/actualbudget/actual/pull/8749) | ✅ **Merged** into `master` | +191 / −6 |
| 2 | [#5525](https://github.com/actualbudget/actual/issues/5525) — shift+click totals wrong with split transactions | [#8748](https://github.com/actualbudget/actual/pull/8748) | 🔄 In review | +74 / −4 |
| 3 | [#8105](https://github.com/actualbudget/actual/issues/8105) — bank sync sends a starting balance of 0 | [#8750](https://github.com/actualbudget/actual/pull/8750) | 🔄 In review | +101 / −23 |

Each contribution has its own writeup in [`writeups/`](writeups/), and the exact commit that
was submitted upstream is preserved as a `git format-patch` file in [`patches/`](patches/).

## Branch-per-fix workflow

Every fix was developed on its own topic branch off upstream `master`, in a personal fork
(`Islinger19/actual`), and submitted as a separate pull request:

```
upstream/master
├── fix-cleanup-pool-negative-balances   → PR #8749  (merged)
├── fix-selected-balance-partial-splits  → PR #8748
└── fix-banksync-custom-start-date       → PR #8750
```

## Reproducing the patches

```bash
git clone https://github.com/actualbudget/actual.git
cd actual
git am < ../patches/<branch>/0001-*.patch
```
