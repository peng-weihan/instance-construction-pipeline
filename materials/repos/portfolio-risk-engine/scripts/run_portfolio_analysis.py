#!/usr/bin/env python
"""End-to-end portfolio risk analysis: construct four portfolios (equal
weight, min-variance, max-Sharpe, risk parity) on a real 8-asset
multi-class universe, compare their risk contributions, compute VaR/CVaR
three independent ways, backtest each construction method with rolling
rebalancing and transaction costs, and stress-test each against the 2008
and 2020 crises. Writes plots/CSVs/summary.json to --outdir.

    python scripts/run_portfolio_analysis.py
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pandas as pd

from portrisk.backtest import performance_stats, rolling_backtest
from portrisk.data import ASSET_CLASS, TICKERS, fetch_prices, price_source, returns_from_prices
from portrisk.optimization import (
    efficient_frontier,
    equal_weight,
    max_sharpe_weights,
    min_variance_weights,
    portfolio_stats,
    risk_contributions,
    risk_parity_weights,
)
from portrisk.plotting import (
    plot_backtest_equity_curves,
    plot_efficient_frontier,
    plot_risk_contributions,
    plot_stress_test,
    plot_var_cvar_comparison,
)
from portrisk.risk_metrics import parametric_var_cvar, simulate_portfolio_returns, var_cvar_from_returns
from portrisk.stress_test import run_all_scenarios


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outdir", type=str, default="results")
    p.add_argument("--lookback-days", type=int, default=252)
    p.add_argument("--rebalance-days", type=int, default=63)
    p.add_argument("--transaction-cost-bps", type=float, default=5.0)
    p.add_argument("--var-alpha", type=float, default=0.05)
    p.add_argument("--force-refresh", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    cache_path = os.path.join(args.outdir, "prices.csv")

    print("Fetching price data...")
    prices = fetch_prices(cache_path, force_refresh=args.force_refresh)
    returns = returns_from_prices(prices)
    source = price_source(cache_path)
    print(f"  {len(prices)} days, {prices.index[0].date()} to {prices.index[-1].date()}, source={source}")

    mu = returns.mean().to_numpy()
    cov = returns.cov().to_numpy()
    asset_names = list(returns.columns)

    # --- Named portfolios (full-sample estimate) ---
    portfolios = {
        "Equal Weight": equal_weight(len(asset_names)),
        "Min Variance": min_variance_weights(cov),
        "Max Sharpe": max_sharpe_weights(mu, cov),
        "Risk Parity": risk_parity_weights(cov),
    }
    weights_df = pd.DataFrame(portfolios, index=asset_names)
    weights_df.to_csv(os.path.join(args.outdir, "portfolio_weights.csv"))
    print("\n--- Portfolio weights ---")
    print(weights_df.round(3).to_string())

    stats_rows = {}
    for name, w in portfolios.items():
        ret, vol = portfolio_stats(w, mu, cov)
        stats_rows[name] = {"ann_return": ret * 252, "ann_vol": vol * np.sqrt(252), "sharpe": (ret * 252) / (vol * np.sqrt(252))}
    stats_df = pd.DataFrame(stats_rows).T
    print("\n--- Portfolio stats (annualized, full-sample) ---")
    print(stats_df.round(3).to_string())

    # --- Efficient frontier ---
    frontier = efficient_frontier(mu, cov, n_points=30)
    named_points = {name: portfolio_stats(w, mu, cov) for name, w in portfolios.items()}
    plot_efficient_frontier(frontier, named_points, os.path.join(args.outdir, "efficient_frontier.png"))

    # --- Risk contributions ---
    rc_pct = {}
    for name, w in portfolios.items():
        rc = risk_contributions(w, cov)
        rc_pct[name] = 100 * rc / rc.sum()
    plot_risk_contributions(rc_pct, asset_names, os.path.join(args.outdir, "risk_contributions.png"))

    # --- VaR/CVaR, three ways, for Max Sharpe and Risk Parity ---
    print(f"\n--- VaR/CVaR at {int((1-args.var_alpha)*100)}% confidence, 1-day ---")
    var_cvar_results = {}
    for name in ("Max Sharpe", "Risk Parity"):
        w = portfolios[name]
        ret_p, vol_p = portfolio_stats(w, mu, cov)
        param = parametric_var_cvar(ret_p, vol_p, alpha=args.var_alpha)
        hist_returns = returns.to_numpy() @ w
        hist = var_cvar_from_returns(hist_returns, alpha=args.var_alpha)
        sim_returns = simulate_portfolio_returns(mu, cov, w, n_sims=500_000, seed=42)
        mc = var_cvar_from_returns(sim_returns, alpha=args.var_alpha)
        var_cvar_results[name] = {"Parametric": param, "Historical": hist, "Monte Carlo": mc}
        print(f"{name}:")
        for method, (v, c) in var_cvar_results[name].items():
            print(f"  {method:12s}  VaR={v*100:.3f}%  CVaR={c*100:.3f}%")
    plot_var_cvar_comparison(var_cvar_results, os.path.join(args.outdir, "var_cvar_comparison.png"))

    # --- Backtest ---
    print(f"\nBacktesting (lookback={args.lookback_days}d, rebalance every {args.rebalance_days}d, "
          f"cost={args.transaction_cost_bps}bps)...")
    weight_fns = {
        "Equal Weight": lambda mu_, cov_: equal_weight(len(asset_names)),
        "Min Variance": lambda mu_, cov_: min_variance_weights(cov_),
        "Max Sharpe": lambda mu_, cov_: max_sharpe_weights(mu_, cov_),
        "Risk Parity": lambda mu_, cov_: risk_parity_weights(cov_),
    }
    backtest_results = {}
    backtest_stats = {}
    for name, fn in weight_fns.items():
        result = rolling_backtest(returns, fn, lookback_days=args.lookback_days,
                                    rebalance_freq_days=args.rebalance_days,
                                    transaction_cost_bps=args.transaction_cost_bps)
        backtest_results[name] = result
        backtest_stats[name] = performance_stats(result["daily"])
    backtest_stats_df = pd.DataFrame(backtest_stats).T
    backtest_stats_df.to_csv(os.path.join(args.outdir, "backtest_stats.csv"))
    print("\n--- Backtest performance (out-of-sample, rolling rebalance) ---")
    print(backtest_stats_df.round(4).to_string())

    plot_backtest_equity_curves(
        {name: r["daily"] for name, r in backtest_results.items()}, os.path.join(args.outdir, "backtest_equity_curves.png")
    )

    # --- Stress tests (full-sample portfolio weights against real crisis windows) ---
    print("\n--- Historical stress tests ---")
    stress_by_portfolio = {}
    for name, w in portfolios.items():
        stress_by_portfolio[name] = run_all_scenarios(returns, w)
        print(f"{name}:")
        print(stress_by_portfolio[name].to_string(index=False))
    plot_stress_test(stress_by_portfolio, os.path.join(args.outdir, "stress_test.png"))

    summary = {
        "data_source": source,
        "n_days": len(prices),
        "date_range": [str(prices.index[0].date()), str(prices.index[-1].date())],
        "asset_classes": ASSET_CLASS,
        "portfolio_weights": {k: dict(zip(asset_names, v.round(4).tolist())) for k, v in portfolios.items()},
        "portfolio_stats": stats_df.round(4).to_dict(orient="index"),
        "var_cvar": {
            name: {method: {"var": v, "cvar": c} for method, (v, c) in methods.items()}
            for name, methods in var_cvar_results.items()
        },
        "backtest_stats": backtest_stats_df.round(4).to_dict(orient="index"),
        "stress_tests": {name: df.set_index("scenario").round(4).to_dict(orient="index")
                           for name, df in stress_by_portfolio.items()},
    }
    with open(os.path.join(args.outdir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nWrote plots/CSVs/summary to {args.outdir}/")


if __name__ == "__main__":
    main()
