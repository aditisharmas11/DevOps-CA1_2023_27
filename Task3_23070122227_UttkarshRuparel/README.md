# Task 3 — OpenTelemetry Collector Contrib: Fix tailsampling error_mode default

**Group members:**
Uttkarsh Ruparel - 23070122227

## Problem Statement

Fix an unset `error_mode` default bug in the OpenTelemetry Collector Contrib
`tailsamplingprocessor`'s `ottl_condition` sampling policy. Previously, an
unset `error_mode` flowed through as an empty string instead of a valid
`ottl.ErrorMode` value, since no explicit default was applied anywhere in
the config path. This PR adds an explicit default (`propagate`, preserving
prior behavior) and introduces a `processor.tailsamplingprocessor.defaultErrorModeIgnore`
feature gate to opt into the recommended `ignore` default, following the
same pattern already shipped in `connector/routing` (#48418).

**Issue:** https://github.com/open-telemetry/opentelemetry-collector-contrib/issues/48420

## Submission

**Upstream Pull Request:** https://github.com/open-telemetry/opentelemetry-collector-contrib/pull/50121

## Summary of changes

- Added `processor.tailsamplingprocessor.defaultErrorModeIgnore` feature gate
  in `metadata.yaml`
- Added `applyOTTLErrorModeDefault` helper in `config.go`, called from
  `Config.Validate()`, to explicitly default `OTTLConditionCfg.ErrorMode`
  based on the gate state
- Added `IsDefaultErrorModeIgnoreEnabled()` in `internal/telemetry/featureflag.go`
- Added `TestApplyOTTLErrorModeDefault` covering all combinations of gate
  state × explicit/unset `error_mode`
- Updated `README.md` to document the new gate and corrected default behavior
- Added changelog entry in `.chloggen/`

## Testing

- `go test ./...` — all tests pass
- `make lint` — clean
