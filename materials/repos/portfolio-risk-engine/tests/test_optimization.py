import numpy as np

from portrisk.optimization import (
    efficient_frontier,
    equal_weight,
    max_sharpe_weights,
    min_variance_weights,
    portfolio_stats,
    risk_contributions,
    risk_parity_weights,
)

# 4 assets, deliberately varied vol/correlation so the three methods
# produce visibly different portfolios rather than all landing near equal weight.
MU = np.array([0.0006, 0.0004, 0.0003, 0.0001])
VOL = np.array([0.020, 0.012, 0.008, 0.004])
CORR = np.array([
    [1.0, 0.6, 0.2, -0.1],
    [0.6, 1.0, 0.3, 0.0],
    [0.2, 0.3, 1.0, 0.1],
    [-0.1, 0.0, 0.1, 1.0],
])
COV = np.outer(VOL, VOL) * CORR


def test_weights_are_long_only_and_sum_to_one():
    for w in (min_variance_weights(COV), max_sharpe_weights(MU, COV), risk_parity_weights(COV)):
        assert abs(w.sum() - 1.0) < 1e-6
        assert (w >= -1e-8).all()


def test_min_variance_beats_equal_weight_on_variance():
    w_mv = min_variance_weights(COV)
    w_eq = equal_weight(4)
    _, vol_mv = portfolio_stats(w_mv, MU, COV)
    _, vol_eq = portfolio_stats(w_eq, MU, COV)
    assert vol_mv <= vol_eq


def test_max_sharpe_beats_equal_weight_on_sharpe():
    w_ms = max_sharpe_weights(MU, COV)
    w_eq = equal_weight(4)
    ret_ms, vol_ms = portfolio_stats(w_ms, MU, COV)
    ret_eq, vol_eq = portfolio_stats(w_eq, MU, COV)
    assert (ret_ms / vol_ms) >= (ret_eq / vol_eq)


def test_risk_parity_gives_roughly_equal_risk_contributions():
    w_rp = risk_parity_weights(COV)
    rc = risk_contributions(w_rp, COV)
    assert (rc.max() - rc.min()) / rc.mean() < 0.02  # within 2% of each other


def test_risk_parity_is_visibly_different_from_min_variance():
    # Sanity that the two methods aren't accidentally coded to do the same
    # thing -- risk parity spreads risk, min-variance minimizes total risk,
    # and on assets this different in vol they shouldn't agree closely.
    w_rp = risk_parity_weights(COV)
    w_mv = min_variance_weights(COV)
    assert np.abs(w_rp - w_mv).sum() > 0.1


def test_efficient_frontier_minimum_matches_min_variance_portfolio():
    frontier = efficient_frontier(MU, COV, n_points=40)
    min_idx = frontier["vol"].idxmin()
    frontier_min_vol = frontier.loc[min_idx, "vol"]

    w_mv = min_variance_weights(COV)
    _, direct_min_vol = portfolio_stats(w_mv, MU, COV)

    assert abs(frontier_min_vol - direct_min_vol) < 5e-4


def test_efficient_frontier_return_grid_spans_asset_range():
    frontier = efficient_frontier(MU, COV, n_points=10)
    assert abs(frontier["target_return"].min() - MU.min()) < 1e-9
    assert abs(frontier["target_return"].max() - MU.max()) < 1e-9
