"""Historical scenario stress testing: replay a real historical window's
actual asset returns against a given (e.g. today's) portfolio weights.

This deliberately does *not* use the covariance-matrix/Monte Carlo
machinery elsewhere in this project. VaR/CVaR answer "how bad could a
normal day be"; a historical scenario answers a different, complementary
question -- "what would have happened to *this exact portfolio* if 2008
happened again" -- using returns that actually occurred, correlations and
all, rather than anything assumed or fitted. That's the standard
distinction between a statistical risk measure and a scenario stress test
in practice.
"""

import numpy as np
import pandas as pd

CRISIS_PERIODS = {
    "2008 Global Financial Crisis": ("2008-09-01", "2009-03-09"),
    "2020 COVID Crash": ("2020-02-19", "2020-03-23"),
}


def apply_scenario(returns: pd.DataFrame, weights: np.ndarray, start: str, end: str) -> dict:
    window = returns.loc[start:end]
    if len(window) == 0:
        raise ValueError(f"no return data in [{start}, {end}] -- check the price history covers this window")
    port_returns = window.to_numpy() @ weights
    # Anchor at 1.0 (the pre-scenario value) before computing the running
    # max -- otherwise the path's own first point trivially becomes its
    # own peak with zero drawdown, hiding a large loss on day one of the
    # scenario. Same fix as backtest.rolling_backtest's anchor row.
    value_path = np.concatenate(([1.0], np.cumprod(1 + port_returns)))
    running_max = np.maximum.accumulate(value_path)
    drawdown = value_path / running_max - 1
    return {
        "cumulative_return": float(value_path[-1] - 1),
        "max_drawdown": float(drawdown.min()),
        "n_trading_days": len(port_returns),
    }


def run_all_scenarios(returns: pd.DataFrame, weights: np.ndarray) -> pd.DataFrame:
    rows = []
    for name, (start, end) in CRISIS_PERIODS.items():
        stats = apply_scenario(returns, weights, start, end)
        rows.append({"scenario": name, **stats})
    return pd.DataFrame(rows)
