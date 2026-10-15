import numpy as np
import pandas as pd
import pytest

from portrisk.stress_test import apply_scenario

DATES = pd.bdate_range("2008-09-01", periods=8)
RETURNS = pd.DataFrame(
    {"A": [-0.05, -0.03, 0.02, -0.08, 0.01, -0.02, -0.04, 0.03], "B": [0.01, 0.00, -0.01, 0.02, 0.00, 0.01, -0.01, 0.02]},
    index=DATES,
)


def test_single_asset_portfolio_matches_that_assets_own_cumulative_return():
    weights = np.array([1.0, 0.0])
    result = apply_scenario(RETURNS, weights, str(DATES[0].date()), str(DATES[-1].date()))
    expected_cumulative = np.prod(1 + RETURNS["A"].to_numpy()) - 1
    assert abs(result["cumulative_return"] - expected_cumulative) < 1e-10


def test_max_drawdown_is_non_positive_and_at_least_as_bad_as_cumulative_loss():
    weights = np.array([0.6, 0.4])
    result = apply_scenario(RETURNS, weights, str(DATES[0].date()), str(DATES[-1].date()))
    assert result["max_drawdown"] <= 0.0
    if result["cumulative_return"] < 0:
        assert result["max_drawdown"] <= result["cumulative_return"] + 1e-9


def test_missing_window_raises():
    with pytest.raises(ValueError):
        apply_scenario(RETURNS, np.array([0.5, 0.5]), "1990-01-01", "1990-02-01")
