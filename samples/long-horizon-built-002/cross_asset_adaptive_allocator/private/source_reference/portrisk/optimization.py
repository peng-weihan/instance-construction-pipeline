"""Portfolio construction: mean-variance (Markowitz) and risk parity.

All solvers are long-only (weights in [0,1], summing to 1) via SLSQP --
the realistic constraint for most real portfolios (no leverage, no
shorting), and the one that actually makes risk parity and mean-variance
produce visibly different portfolios worth comparing. `mu`/`cov` are
expected to be *daily* mean returns / covariance throughout this package;
annualizing is left to the reporting layer (metrics get multiplied by 252
/ sqrt(252) only when displayed) so the optimizers themselves never have
to care about units.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def portfolio_stats(w: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> tuple[float, float]:
    ret = float(w @ mu)
    vol = float(np.sqrt(w @ cov @ w))
    return ret, vol


def equal_weight(n_assets: int) -> np.ndarray:
    return np.full(n_assets, 1.0 / n_assets)


def _solve(objective, n_assets: int, extra_constraints: list | None = None) -> np.ndarray:
    x0 = equal_weight(n_assets)
    bounds = [(0.0, 1.0)] * n_assets
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    if extra_constraints:
        constraints += extra_constraints
    result = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints,
                       options={"maxiter": 500, "ftol": 1e-12})
    if not result.success:
        raise RuntimeError(f"optimizer failed to converge: {result.message}")
    return result.x


def min_variance_weights(cov: np.ndarray) -> np.ndarray:
    n = cov.shape[0]
    return _solve(lambda w: w @ cov @ w, n)


def max_sharpe_weights(mu: np.ndarray, cov: np.ndarray, rf: float = 0.0) -> np.ndarray:
    n = len(mu)

    def neg_sharpe(w):
        ret, vol = portfolio_stats(w, mu, cov)
        return -(ret - rf) / vol

    return _solve(neg_sharpe, n)


def efficient_frontier(mu: np.ndarray, cov: np.ndarray, n_points: int = 25) -> pd.DataFrame:
    """Min-variance weights for a grid of target returns spanning the
    achievable range. Every target in [min(mu), max(mu)] is feasible under
    long-only + sum-to-1, since that's exactly the convex hull of the
    single-asset corner portfolios.
    """
    n = len(mu)
    targets = np.linspace(mu.min(), mu.max(), n_points)
    rows = []
    for target in targets:
        constraints = [{"type": "eq", "fun": lambda w, t=target: w @ mu - t}]
        w = _solve(lambda w: w @ cov @ w, n, extra_constraints=constraints)
        ret, vol = portfolio_stats(w, mu, cov)
        rows.append({"target_return": target, "return": ret, "vol": vol, "weights": w})
    return pd.DataFrame(rows)


def risk_contributions(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Each asset's contribution to total portfolio volatility. Sums to
    the portfolio volatility itself (Euler's theorem for the
    linearly-homogeneous risk measure sqrt(w'Cov w)).
    """
    port_vol = np.sqrt(w @ cov @ w)
    marginal_contribution = (cov @ w) / port_vol
    return w * marginal_contribution


def risk_parity_weights(cov: np.ndarray) -> np.ndarray:
    n = cov.shape[0]

    def objective(w):
        rc = risk_contributions(w, cov)
        target = rc.mean()
        return float(np.sum((rc - target) ** 2))

    return _solve(objective, n)
