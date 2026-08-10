# Contributing

Thanks for helping make agent actions easier to review and constrain.

## Scope

Good contributions are narrow and testable:

- adapters from an existing public agent/tool format into contract version `1`;
- deterministic rules with a concrete unsafe and safe fixture;
- schema clarity and interoperability improvements;
- documentation based on public workflows.

Please do not include private organization policies, internal schemas, credentials, customer data, or unpublished research artifacts.

## Development setup

```bash
git clone https://github.com/njs2017/agent-action-contract.git
cd agent-action-contract
uv sync --group dev
```

## Verification

Run the complete local gate before opening a pull request:

```bash
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv build
```

Behavior changes should include tests that demonstrate the failure before the implementation and pass afterward. New policy rules need a stable rule ID, a precise path, an actionable message, and both positive and negative fixtures.

## Pull requests

Keep pull requests focused. Explain the action workflow being protected, why structural schema validation is insufficient, and how false positives were considered.
