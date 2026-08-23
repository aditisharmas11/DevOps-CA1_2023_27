# Task 3 – Open Source Contribution

## Student Details

- Name: Raghav Dhoot
- Roll Number: 23070122170

- Name: Sukaran Singh
- Roll Number: 23070122213

- Name: Dhruv Gupta
- Roll Number: 23070122258

## Project

pytest

Repository:
https://github.com/pytest-dev/pytest

## Issue

Issue #14909 – MonkeyPatch records stale undo entries when
delattr/setitem/delitem fails

Issue:
https://github.com/pytest-dev/pytest/issues/14909

## Problem Description

The issue was related to pytest's MonkeyPatch implementation.
When an attribute or item mutation failed, the undo information
could still be recorded even though the mutation itself had not
successfully happened. This could leave stale undo entries and
cause incorrect cleanup behaviour.

## Solution

The fix changes the mutation logic so that undo state is recorded
only after the corresponding mutation succeeds.

Regression tests were added for the affected operations:
- delattr
- setitem
- delitem

## Testing

The relevant pytest test suite was executed.

Result:
37 passed, 2 skipped.

## Upstream Pull Request

https://github.com/pytest-dev/pytest/pull/14927

## Conclusion

The issue was reproduced, the implementation was fixed, and
regression tests were added to verify the corrected behaviour.
The fix was submitted to the upstream pytest repository through
Pull Request #14927.
