"""Rolling out-of-sample backtest: periodically re-optimize on a trailing
window, hold the resulting weights (letting them drift with asset returns)
until the next rebalance, and charge a transaction cost proportional to
turnover each time the portfolio is rebalanced.

This is a genuinely sequential process -- each day's portfolio value
depends on the previous day's drifted weights, which depend on the whole
history since the last rebalance -- so unlike the batch Monte Carlo
elsewhere in this project's sibling repos, there's no independent "many
parallel trials" axis to vectorize across: it's one portfolio, one path
through time. A plain day-by-day loop over a few thousand trading days
runs in well under a second, so forcing this into a vectorized form would
trade clarity for a speedup nothing here actually needs.
"""

import numpy as np
import pandas as pd


def rolling_backtest(
    returns: pd.DataFrame, weight_fn, lookback_days: int = 252, rebalance_freq_days: int = 63,
    transaction_cost_bps: float = 5.0, initial_value: float = 100.0,
) -> dict:
    """`weight_fn(mu, cov) -> weights` is called at every rebalance with the
    trailing-window mean/covariance. Returns a dict with a daily value/
    turnover DataFrame and the weight history at each rebalance date.
    """
    dates = returns.index
    n_assets = returns.shape[1]
    # Anchor the recorded series at the true pre-backtest value (date =
    # last day of the lookback window). Without this anchor, the first
    # *recorded* value would itself become the reference point for
    # drawdown (via cummax) and CAGR -- silently hiding any loss on the
    # very first simulated day, since a series' own first point always has
    # zero drawdown from itself.
    values = [initial_value]
    turnovers = [0.0]
    index = [dates[lookback_days - 1]]
    weight_history = []

    current_value = initial_value
    drifted_weights = None

    for i in range(lookback_days, len(dates)):
        is_rebalance = (i - lookback_days) % rebalance_freq_days == 0
        turnover = 0.0

        if is_rebalance:
            window = returns.iloc[i - lookback_days : i]
            mu = window.mean().to_numpy()
            cov = window.cov().to_numpy()
            target_weights = weight_fn(mu, cov)
            prior_weights = drifted_weights if drifted_weights is not None else np.zeros(n_assets)
            turnover = float(np.sum(np.abs(target_weights - prior_weights)))
            current_value *= 1 - (transaction_cost_bps / 10_000) * turnover
            drifted_weights = target_weights.copy()
            weight_history.append({"date": dates[i], "weights": target_weights.copy()})

        day_return = returns.iloc[i].to_numpy()
        port_return = float(drifted_weights @ day_return)
        current_value *= 1 + port_return

        grown = drifted_weights * (1 + day_return)
        drifted_weights = grown / grown.sum()

        values.append(current_value)
        turnovers.append(turnover)
        index.append(dates[i])

    daily = pd.DataFrame({"value": values, "turnover": turnovers}, index=pd.DatetimeIndex(index, name="date"))
    return {"daily": daily, "weight_history": weight_history}


def performance_stats(daily: pd.DataFrame) -> dict:
    value = daily["value"]
    daily_returns = value.pct_change().dropna()
    n_years = len(value) / 252
    cagr = (value.iloc[-1] / value.iloc[0]) ** (1 / n_years) - 1
    ann_vol = daily_returns.std(ddof=1) * np.sqrt(252)
    sharpe = (daily_returns.mean() * 252) / ann_vol
    running_max = value.cummax()
    drawdown = value / running_max - 1
    max_drawdown = drawdown.min()
    total_turnover = daily["turnover"].sum()
    return {
        "cagr": float(cagr), "ann_vol": float(ann_vol), "sharpe": float(sharpe),
        "max_drawdown": float(max_drawdown), "total_turnover": float(total_turnover),
    }
