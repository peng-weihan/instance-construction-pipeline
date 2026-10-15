"""Report plots. Agg backend so this renders headless."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot_efficient_frontier(frontier_df, named_portfolios: dict, path: str) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.plot(frontier_df["vol"] * np.sqrt(252) * 100, frontier_df["return"] * 252 * 100,
            color="gray", linewidth=1.5, label="Efficient frontier", zorder=1)
    colors = plt.cm.Set1(np.linspace(0, 0.5, len(named_portfolios)))
    for (name, (ret, vol)), color in zip(named_portfolios.items(), colors):
        ax.scatter(vol * np.sqrt(252) * 100, ret * 252 * 100, s=90, color=color, label=name, zorder=3, edgecolor="black")
    ax.set_xlabel("Annualized volatility (%)")
    ax.set_ylabel("Annualized return (%)")
    ax.set_title("Efficient frontier and named portfolios")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_risk_contributions(portfolios: dict, asset_names: list, path: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    n_portfolios = len(portfolios)
    n_assets = len(asset_names)
    x = np.arange(n_portfolios)
    bottom = np.zeros(n_portfolios)
    colors = plt.cm.tab10(np.linspace(0, 1, n_assets))
    rc_matrix = np.array([rc_pct for rc_pct in portfolios.values()])  # (n_portfolios, n_assets), already %
    for j, asset in enumerate(asset_names):
        ax.bar(x, rc_matrix[:, j], bottom=bottom, color=colors[j], label=asset)
        bottom += rc_matrix[:, j]
    ax.set_xticks(x)
    ax.set_xticklabels(list(portfolios.keys()))
    ax.set_ylabel("Share of portfolio risk (%)")
    ax.set_title("Risk contribution by asset, across portfolio construction methods")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_var_cvar_comparison(results: dict, path: str) -> None:
    """results: {portfolio_name: {method: (var, cvar)}}"""
    portfolio_names = list(results.keys())
    methods = list(next(iter(results.values())).keys())
    fig, axes = plt.subplots(1, len(portfolio_names), figsize=(4.5 * len(portfolio_names), 4.5), sharey=True)
    if len(portfolio_names) == 1:
        axes = [axes]
    width = 0.35
    x = np.arange(len(methods))
    for ax, pname in zip(axes, portfolio_names):
        vars_ = [results[pname][m][0] * 100 for m in methods]
        cvars = [results[pname][m][1] * 100 for m in methods]
        ax.bar(x - width / 2, vars_, width, label="VaR", color="#1f6f8b")
        ax.bar(x + width / 2, cvars, width, label="CVaR", color="#c1440e")
        ax.set_xticks(x)
        ax.set_xticklabels(methods, rotation=20, ha="right")
        ax.set_title(pname, fontsize=10)
        ax.grid(alpha=0.3, axis="y")
    axes[0].set_ylabel("1-day 95% loss (%)")
    axes[0].legend()
    fig.suptitle("VaR / CVaR by method and portfolio")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_backtest_equity_curves(daily_dfs: dict, path: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    for name, daily in daily_dfs.items():
        ax.plot(daily.index, daily["value"], label=name, linewidth=1.3)
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio value (start = 100)")
    ax.set_title("Backtested equity curves (net of transaction costs)")
    ax.set_yscale("log")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_stress_test(stress_by_portfolio: dict, path: str) -> None:
    scenario_names = list(next(iter(stress_by_portfolio.values()))["scenario"])
    portfolio_names = list(stress_by_portfolio.keys())
    x = np.arange(len(scenario_names))
    width = 0.8 / len(portfolio_names)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = plt.cm.Set1(np.linspace(0, 0.5, len(portfolio_names)))
    for i, (name, df) in enumerate(stress_by_portfolio.items()):
        ax.bar(x + i * width, df["max_drawdown"] * 100, width, label=name, color=colors[i])
    ax.set_xticks(x + width * (len(portfolio_names) - 1) / 2)
    ax.set_xticklabels(scenario_names)
    ax.set_ylabel("Max drawdown during scenario (%)")
    ax.set_title("Historical stress test: max drawdown by portfolio")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
