"""Value at Risk and Conditional VaR (Expected Shortfall), three ways.

Both VaR and CVaR are returned as *positive* numbers representing a loss
magnitude -- "95% 1-day VaR of 2.1%" means a 2.1% loss, not -2.1% return.

Parametric (variance-covariance): assumes portfolio returns are normal,
r ~ N(mu_p, sigma_p^2), and uses the closed-form normal quantile / normal
expected-shortfall formulas directly. Fast, and exactly as good as the
normality assumption -- which real returns don't satisfy (see the
historical-vs-parametric comparison in run_portfolio_analysis.py).

Historical simulation and Monte Carlo share one function
(`var_cvar_from_returns`): both are "take a series of portfolio returns
and read off the empirical tail," differing only in whether that series
was actually observed (historical) or drawn from a fitted multivariate
normal (Monte Carlo, via `simulate_portfolio_returns`). Monte Carlo VaR
should converge to the parametric formula as n_sims grows, since it's
sampling from the exact same normal assumption -- that convergence is
itself a check that both are implemented correctly (see
test_risk_metrics.py), the same cross-validation-between-methods approach
used for the option pricers in the options-pricing project.
"""

import numpy as np
from scipy.stats import norm


def parametric_var_cvar(mu_p: float, sigma_p: float, alpha: float = 0.05) -> tuple[float, float]:
    z = norm.ppf(alpha)
    var = -(mu_p + z * sigma_p)
    cvar = -(mu_p - sigma_p * norm.pdf(z) / alpha)
    return var, cvar


def var_cvar_from_returns(returns: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    threshold = np.percentile(returns, alpha * 100)
    var = -threshold
    tail = returns[returns <= threshold]
    cvar = -tail.mean()
    return var, cvar


def simulate_portfolio_returns(mu: np.ndarray, cov: np.ndarray, w: np.ndarray, n_sims: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    asset_returns = rng.multivariate_normal(mu, cov, size=n_sims)
    return asset_returns @ w
