"""Multi-asset daily price data: a real fetch when network access is
available, a synthetic-but-correlated dataset when it isn't.

Universe is eight liquid ETFs spanning distinct asset classes -- chosen
specifically so the covariance matrix has real, exploitable structure
(equities correlated with each other, bonds/gold anti-correlated with
equities in stress periods) rather than eight nearly-identical large-cap
funds that would make every portfolio construction method converge to
roughly the same answer:

  SPY  US large-cap equity        EEM  emerging-market equity
  IWM  US small-cap equity        TLT  long-term US Treasuries
  EFA  developed intl equity      GLD  gold
  VNQ  US real estate (REITs)     DBC  broad commodities

All eight have price history back to at least 2006, which matters: the
2008 crisis stress test (stress_test.py) needs real data spanning it, not
just a recent window.
"""

import os

import numpy as np
import pandas as pd

TICKERS = ["SPY", "IWM", "EFA", "EEM", "TLT", "GLD", "VNQ", "DBC"]
ASSET_CLASS = {
    "SPY": "US Large Cap", "IWM": "US Small Cap", "EFA": "Intl Developed", "EEM": "Emerging Mkts",
    "TLT": "Long Treasuries", "GLD": "Gold", "VNQ": "US REITs", "DBC": "Commodities",
}
START_DATE = "2006-06-01"


def fetch_prices(cache_path: str = "results/prices.csv", force_refresh: bool = False) -> pd.DataFrame:
    """Returns a DataFrame of daily adjusted close prices, tickers as
    columns, indexed by date. A `source` sidecar file records whether this
    came from a live fetch or the synthetic fallback.
    """
    source_path = cache_path.replace(".csv", "_source.txt")
    if os.path.exists(cache_path) and not force_refresh:
        prices = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return prices

    try:
        prices = _fetch_live()
        source = "yfinance"
    except Exception as e:
        print(f"  live fetch failed ({e!r}); falling back to a synthetic correlated dataset")
        prices = _synthetic_prices()
        source = "synthetic"

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    prices.to_csv(cache_path)
    with open(source_path, "w") as f:
        f.write(source)
    return prices


def price_source(cache_path: str = "results/prices.csv") -> str:
    source_path = cache_path.replace(".csv", "_source.txt")
    if os.path.exists(source_path):
        return open(source_path).read().strip()
    return "unknown"


def _fetch_live() -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(TICKERS, start=START_DATE, auto_adjust=True, progress=False)["Close"]
    prices = raw[TICKERS].dropna(how="any")
    if len(prices) < 500:
        raise RuntimeError(f"only {len(prices)} rows of overlapping data -- fetch likely partial/failed")
    return prices


def _synthetic_prices(seed: int = 0) -> pd.DataFrame:
    """Multivariate-normal daily returns with a stylized asset-class
    correlation structure (equities correlated with each other, bonds/gold
    weakly-to-negatively correlated with equities, commodities in between)
    -- not calibrated to real numbers, just plausible enough that every
    downstream module still runs end to end offline.
    """
    rng = np.random.default_rng(seed)
    n_assets = len(TICKERS)
    dates = pd.bdate_range(START_DATE, periods=5000)

    annual_vol = np.array([0.18, 0.22, 0.19, 0.24, 0.11, 0.16, 0.20, 0.17])
    annual_mean = np.array([0.09, 0.08, 0.06, 0.07, 0.03, 0.05, 0.07, 0.04])
    corr = np.array([
        # SPY   IWM   EFA   EEM   TLT   GLD   VNQ   DBC
        [1.00, 0.85, 0.80, 0.65, -0.30, 0.05, 0.65, 0.35],
        [0.85, 1.00, 0.70, 0.60, -0.25, 0.00, 0.60, 0.30],
        [0.80, 0.70, 1.00, 0.75, -0.20, 0.10, 0.55, 0.35],
        [0.65, 0.60, 0.75, 1.00, -0.15, 0.15, 0.50, 0.40],
        [-0.30, -0.25, -0.20, -0.15, 1.00, 0.20, -0.10, -0.05],
        [0.05, 0.00, 0.10, 0.15, 0.20, 1.00, 0.10, 0.30],
        [0.65, 0.60, 0.55, 0.50, -0.10, 0.10, 1.00, 0.30],
        [0.35, 0.30, 0.35, 0.40, -0.05, 0.30, 0.30, 1.00],
    ])
    daily_vol = annual_vol / np.sqrt(252)
    daily_mean = annual_mean / 252
    cov = np.outer(daily_vol, daily_vol) * corr

    daily_returns = rng.multivariate_normal(daily_mean, cov, size=len(dates))
    prices = 100 * np.exp(np.cumsum(daily_returns, axis=0))
    return pd.DataFrame(prices, index=dates, columns=TICKERS)


def returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna(how="any")
