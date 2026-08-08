"""Generate the tiny committed CSV fixtures used by the test suite.

Run from the repo root:
    PYTHONPATH=. .venv/bin/python tests/fixtures/make_fixtures.py

Regeneration is deterministic. The committed CSVs are the fixture contract — if a change
here alters them, review the diff.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FIXTURES_DIR = Path(__file__).resolve().parent
N_TRAIN = 60
N_TEST = 20
SEED = 7
HIGH_CARD_LEVELS = [f"L{index:02d}" for index in range(18)]


def _features(rng: np.random.Generator, n: int) -> pd.DataFrame:
    """Build the shared 4-numeric / 2-categorical feature frame."""
    return pd.DataFrame(
        {
            "n1": rng.normal(0.0, 1.0, n).round(3),
            "n2": rng.normal(5.0, 2.0, n).round(3),
            "n3": rng.integers(0, 50, n).astype(float),
            "n4": rng.uniform(0.0, 1.0, n).round(3),
            "c1": rng.choice(["a", "b", "c"], n),
            "c2": [HIGH_CARD_LEVELS[index % len(HIGH_CARD_LEVELS)] for index in range(n)],
        }
    )


def _inject_nans(frame: pd.DataFrame) -> pd.DataFrame:
    """Put NaNs at fixed positions so imputation is always exercised."""
    frame = frame.copy()
    frame.loc[frame.index[0:3], "n1"] = np.nan
    frame.loc[frame.index[4:6], "n2"] = np.nan
    frame.loc[frame.index[7], "c1"] = np.nan
    return frame


def _signal(frame: pd.DataFrame) -> pd.Series:
    """A learnable function of the features, so trees find splits on tiny data."""
    return (
        1.8 * frame["n1"].fillna(0.0)
        - 0.9 * (frame["n2"].fillna(5.0) - 5.0)
        + 0.7 * (frame["c1"] == "a").astype(float)
        + 0.02 * frame["n3"]
    )


def _write(directory: Path, frames: dict[str, pd.DataFrame]) -> None:
    """Write each frame as <name>.csv into directory."""
    directory.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(directory / f"{name}.csv", index=False)


def build_clf() -> None:
    """Binary-classification fixture: ID `id`, target `target`."""
    rng = np.random.default_rng(SEED)
    train = _inject_nans(_features(rng, N_TRAIN))
    test = _inject_nans(_features(rng, N_TEST))
    test.loc[test.index[0], "c1"] = "z"
    score = _signal(train)
    train.insert(0, "id", range(N_TRAIN))
    train["target"] = (score > score.median()).astype(int).to_numpy()
    test.insert(0, "id", range(100, 100 + N_TEST))
    submission = pd.DataFrame({"id": test["id"].to_numpy(), "target": 0.5})
    _write(FIXTURES_DIR / "clf", {"train": train, "test": test, "sample_submission": submission})


def build_reg() -> None:
    """Regression fixture: ID `row_id`, target `score`."""
    rng = np.random.default_rng(SEED + 1)
    train = _inject_nans(_features(rng, N_TRAIN))
    test = _inject_nans(_features(rng, N_TEST))
    test.loc[test.index[0], "c1"] = "z"
    values = (_signal(train) + rng.normal(0.0, 0.5, N_TRAIN)).round(4)
    train.insert(0, "row_id", range(N_TRAIN))
    train["score"] = values.to_numpy()
    test.insert(0, "row_id", range(100, 100 + N_TEST))
    submission = pd.DataFrame({"row_id": test["row_id"].to_numpy(), "score": 0.0})
    _write(FIXTURES_DIR / "reg", {"train": train, "test": test, "sample_submission": submission})


if __name__ == "__main__":
    build_clf()
    build_reg()
    print(f"fixtures written to {FIXTURES_DIR}")
