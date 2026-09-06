# Open Source Contribution Submission - Group 2

- **Contributors:**
  - Eccha Bansal Agrawal -23070122264
  - Aarya Balwadkar - 23070122005

- **Target Repository:** [ray-project/kuberay](https://github.com/ray-project/kuberay)
- **Target Issue:** [KubeRay Issue #5026](https://github.com/ray-project/kuberay/issues/5026)
- **KubeRay PR:** [PR #5115](https://github.com/ray-project/kuberay/pull/5115)

### Summary of Work Done

Moved the autoscaler-dependent **Node Count** panel into a collapsed **Autoscaling** section in the KubeRay Grafana dashboard.

This prevents the default dashboard from displaying an empty or misleading Node Count panel when autoscaling is disabled, while preserving the existing panel configuration and queries.

### Verification

- JSON validation passed.
- Node Count was moved inside the collapsed Autoscaling section.
- `git diff --check` passed.