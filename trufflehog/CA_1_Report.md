# Open Source Contribution Report for CA 1
### Improving Secret-Verification Reliability in TruffleHog

| | |
|---|---|
| **Project** | TruffleHog , trufflesecurity/trufflehog |
| **Contribution type** | Bug fix / reliability improvement (open-source community contribution) |
| **Pull Request** | [#5227 , fix(detectors): report Unsplash verifier errors](https://github.com/trufflesecurity/trufflehog/pull/5227) |
| **Related issue** | [#4051 , Improve Detectors Verification Logic and Error Handling](https://github.com/trufflesecurity/trufflehog/issues/4051) |
| **Status** | Open , passed all automated checks (CLA, code review bot, security scans); awaiting maintainer code-owner review |
| **File changed** | `pkg/detectors/unsplash/unsplash.go` (+11 / -1 lines) |

---

## 1. Project Background

TruffleHog is a widely used, open-source secret-scanning tool (27,000+ GitHub stars) that scans codebases, repositories, and file systems for accidentally committed credentials , API keys, tokens, and passwords. A core part of its value proposition is not just detecting a potential secret via pattern matching, but **verifying** whether that secret is actually live by making a real request to the corresponding service's API. This distinguishes TruffleHog from simple regex-based scanners: a result marked "Verified" tells a security team the credential is confirmed active and must be rotated immediately, which is critical for prioritising incident response.

## 2. Problem Identified

The maintainers had flagged, in a long-running community issue ([#4051](https://github.com/trufflesecurity/trufflehog/issues/4051)), that many of TruffleHog's ~800+ individual "detectors" (one per supported service) shared a structurally weak verification pattern:

```go
if err == nil {
    defer res.Body.Close()
    if res.StatusCode >= 200 && res.StatusCode < 300 {
        s1.Verified = true
    }
}
```

This pattern has three concrete shortcomings:

- **Silent failure:** Network or request errors are silently discarded , nothing is logged or surfaced, making failures invisible.
- **No status differentiation:** Non-2xx responses (e.g. 401 Unauthorized, 403 Forbidden) are all treated identically to "could not verify," with no distinction between "this key is confirmed invalid" and "the check itself failed for an unrelated reason."
- **No error surfacing:** There is no mechanism to report a meaningful verification error back to the user, so a scan can under-report or mis-classify a real secret with no diagnostic trail.

I audited the codebase directly (grepping all ~885 detector implementations under `pkg/detectors/`) and confirmed the Unsplash detector was one of more than 40 detectors still exhibiting this exact unfixed pattern.

## 3. My Contribution

### 3.1 Investigation and validation

Before writing any code, I read the maintainers' own reference pull requests (linked from the issue) to understand the expected fix shape, and examined an already-fixed detector (Klaviyo) to confirm the idiomatic pattern the project wanted.

I then tested the real Unsplash API directly with both a valid and an invalid API key, to confirm the actual HTTP status codes returned in practice rather than assuming them from documentation:

```
$ curl -i "https://api.unsplash.com/photos/?client_id=<valid_key>"
HTTP/2 200                                    (confirmed)

$ curl -i "https://api.unsplash.com/photos/?client_id=<invalid_key>"
HTTP/2 401                                    (confirmed)
```

This step mattered: had Unsplash returned 403 instead of 401 for invalid keys (as some APIs do), the fix would need different status-code branching. Verifying against the live API rather than assuming avoided shipping an incorrect fix.

### 3.2 Verification of the fix

- **Build:** Compiled cleanly across the full module (`go build ./...`).
- **Tests:** Existing detector unit tests pass unchanged (`go test ./pkg/detectors/unsplash/...`), confirming the regex-matching behaviour was untouched.
- **Static analysis:** No warnings raised (`go vet ./pkg/detectors/unsplash/...`).
- **Manual API validation:** Verified against Unsplash's live API as described in 3.1, confirming the new branching logic matches real-world responses.
- **CI checks:** Automated checks on the submitted PR , CLA sign-off, an AI code-review bot (Cursor Bugbot), and two Socket Security supply-chain scans , all passed before human review.

## 4. Impact on the Tool

Although the change is small in size (11 lines added, 1 removed, one file), its impact is representative of a broader reliability class of fix that the maintainers explicitly flagged as important across the entire codebase:

- **Reduces false negatives:** Previously, a network failure or an unexpected server error (e.g. a 500 or a rate-limit response) during verification was indistinguishable from "the key is invalid." A security team relying on TruffleHog's output could wrongly conclude a live credential was safe, simply because the verification check itself failed silently. The fix ensures such cases are now reported as explicit verification errors rather than false negatives.
- **Improves diagnostic signal:** Downstream consumers of scan results (dashboards, CI gates, alerting pipelines) can now distinguish three states , verified, confirmed invalid, and "verification failed / inconclusive" , instead of collapsing the latter two together.
- **Consistent with project conventions:** The fix follows an established pattern used across dozens of other detectors in the codebase, meaning it integrates consistently with the project's existing conventions and required no architectural changes.
- **Part of a larger reliability initiative:** The parent issue (#4051) is an active, ongoing community effort; this contribution is one of a continuing series of detector-level fixes submitted by multiple contributors over the past year, incrementally raising the reliability of TruffleHog's verification logic across its entire detector library.

## 5. Skills Demonstrated

- **Technical:** Cloning, building, and testing a large-scale Go codebase (open-source secret-scanning tool).
- **Open-source practice:** Reading maintainer guidance and prior reference PRs to match an established code convention rather than inventing a new one.
- **Engineering rigor:** Validating assumptions against a live third-party API before writing or trusting a fix, instead of relying on documentation alone.
- **Version control:** Following Git/GitHub workflow conventions: forking, feature branching, descriptive commit messages, and a PR description that clearly explains before/after behaviour and testing evidence.
- **Collaboration:** Understood and respected the umbrella-issue etiquette (mentioning rather than closing the parent issue, keeping the PR scoped to a single detector) to avoid disrupting an active multi-contributor effort.

## 6. Current Status and Next Steps

Pull request [#5227](https://github.com/trufflesecurity/trufflehog/pull/5227) is open against `trufflesecurity/trufflehog:main` and has passed all automated checks (CLA verification, AI code review, and security scanning). It is currently awaiting a required code-owner review from the `trufflesecurity/integrations` team before it can be merged, per the repository's branch protection rules. Following this contribution, I intend to submit further independent detector-level fixes under the same umbrella issue (#4051), continuing to reduce the number of TruffleHog detectors still affected by the identified verification weakness.

---

## References

- Pull Request: https://github.com/trufflesecurity/trufflehog/pull/5227
- Related Issue: https://github.com/trufflesecurity/trufflehog/issues/4051
- Project Repository: https://github.com/trufflesecurity/trufflehog


