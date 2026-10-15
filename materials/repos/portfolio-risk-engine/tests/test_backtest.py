import numpy as np
import pandas as pd

from portrisk.backtest import performance_stats, rolling_backtest

DATES = pd.bdate_range("2020-01-01", periods=10)
RETURNS = pd.DataFrame(
    {
        "A": [0.01, -0.02, 0.03, 0.00, 0.01, -0.01, 0.02, 0.01, -0.03, 0.02],
        "B": [0.00, 0.01, -0.01, 0.02, 0.00, 0.01, -0.02, 0.03, 0.01, -0.01],
    },
    index=DATES,
)

FIXED_5050 = lambda mu, cov: np.array([0.5, 0.5])


def test_daily_rebalance_matches_simple_weighted_compounding():
    # With rebalance every single day, weights never get a chance to drift
    # away from target -- the whole engine should collapse to the trivial
    # "compound the fixed-weight daily return" formula, which is easy to
    # verify independently of the backtest machinery.
    result = rolling_backtest(RETURNS, FIXED_5050, lookback_days=2, rebalance_freq_days=1, transaction_cost_bps=0.0)
    expected_port_returns = 0.5 * RETURNS["A"].iloc[2:] + 0.5 * RETURNS["B"].iloc[2:]
    expected_value = 100.0 * np.cumprod(1 + expected_port_returns.to_numpy())
    # First row is the anchor (the pre-backtest value, date = last lookback day);
    # everything after it should match the simple weighted-compounding formula.
    assert result["daily"]["value"].iloc[0] == 100.0
    assert np.allclose(result["daily"]["value"].to_numpy()[1:], expected_value)


def test_transaction_costs_strictly_reduce_terminal_value():
    no_cost = rolling_backtest(RETURNS, FIXED_5050, lookback_days=2, rebalance_freq_days=1, transaction_cost_bps=0.0)
    with_cost = rolling_backtest(RETURNS, FIXED_5050, lookback_days=2, rebalance_freq_days=1, transaction_cost_bps=50.0)
    assert with_cost["daily"]["value"].iloc[-1] < no_cost["daily"]["value"].iloc[-1]


def test_weights_drift_between_infrequent_rebalances():
    # rebalance_freq_days=10 (longer than the whole test series) means only
    # one rebalance ever happens -- turnover should be recorded exactly once.
    result = rolling_backtest(RETURNS, FIXED_5050, lookback_days=2, rebalance_freq_days=10, transaction_cost_bps=0.0)
    n_rebalances = (result["daily"]["turnover"] > 0).sum()
    assert n_rebalances == 1


def test_performance_stats_cagr_on_a_doubling_series():
    value = pd.Series(np.geomspace(100, 200, 252))  # exactly 252 daily steps, doubles over 1 year
    daily = pd.DataFrame({"value": value, "turnover": np.zeros(len(value))})
    stats = performance_stats(daily)
    assert abs(stats["cagr"] - 1.0) < 0.01
    assert stats["max_drawdown"] <= 0.0
