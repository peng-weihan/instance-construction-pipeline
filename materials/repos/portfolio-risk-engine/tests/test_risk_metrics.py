import numpy as np

from portrisk.risk_metrics import parametric_var_cvar, simulate_portfolio_returns, var_cvar_from_returns


def test_cvar_is_always_at_least_var():
    var, cvar = parametric_var_cvar(mu_p=0.0005, sigma_p=0.01, alpha=0.05)
    assert cvar >= var

    rng = np.random.default_rng(0)
    returns = rng.standard_normal(5000) * 0.01 + 0.0003
    var_h, cvar_h = var_cvar_from_returns(returns, alpha=0.05)
    assert cvar_h >= var_h


def test_parametric_matches_known_standard_normal_values():
    # For a standard normal (mu=0, sigma=1), 95% VaR/CVaR have well-known values.
    var, cvar = parametric_var_cvar(mu_p=0.0, sigma_p=1.0, alpha=0.05)
    assert abs(var - 1.645) < 0.01
    assert abs(cvar - 2.063) < 0.01


def test_monte_carlo_converges_to_parametric():
    mu = np.array([0.0005, 0.0003])
    cov = np.array([[0.0004, 0.0001], [0.0001, 0.0002]])
    w = np.array([0.6, 0.4])
    mu_p = float(w @ mu)
    sigma_p = float(np.sqrt(w @ cov @ w))

    param_var, param_cvar = parametric_var_cvar(mu_p, sigma_p, alpha=0.05)
    sim_returns = simulate_portfolio_returns(mu, cov, w, n_sims=500_000, seed=1)
    mc_var, mc_cvar = var_cvar_from_returns(sim_returns, alpha=0.05)

    assert abs(mc_var - param_var) < 0.0005
    assert abs(mc_cvar - param_cvar) < 0.0008


def test_historical_var_recovers_parametric_on_synthetic_normal_data():
    rng = np.random.default_rng(2)
    mu_p, sigma_p = 0.0004, 0.012
    returns = rng.standard_normal(200_000) * sigma_p + mu_p
    param_var, param_cvar = parametric_var_cvar(mu_p, sigma_p, alpha=0.05)
    hist_var, hist_cvar = var_cvar_from_returns(returns, alpha=0.05)
    assert abs(hist_var - param_var) < 0.0005
    assert abs(hist_cvar - param_cvar) < 0.0008
