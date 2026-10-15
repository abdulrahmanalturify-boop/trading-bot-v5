"""Out-of-sample validation helpers for TURA's research workflows.

These helpers do NOT generate trade signals or send orders. Splits have a
deliberate time gap so a strategy/model fitted using forward-return labels
cannot accidentally use outcomes still unknown at a test decision time.

Choose `gap` >= the *maximum* horizon of your training labels (including
the fill delay). Passing this helper alone does not remove survivorship bias,
cross-sectional leakage, or point-in-time fundamental-data issues.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class WalkForwardWindow:
    train_start: int
    train_stop: int
    test_start: int
    test_stop: int

    @property
    def train(self):
        return slice(self.train_start, self.train_stop)

    @property
    def test(self):
        return slice(self.test_start, self.test_stop)


def embargoed_walk_forward(n_rows, train_size=504, test_size=63, gap=10,
                          step=None, expanding=True):
    """Yield chronological, non-overlapping train/test slices.

    All ranges follow Python's [start, stop) convention. A gap separates
    each training window from its test period. With a rolling window the
    training history stays `train_size` rows; expanding mode starts at zero.
    No parameter is selected from the test fold.
    """
    for name, value in (("n_rows", n_rows), ("train_size", train_size),
                        ("test_size", test_size), ("gap", gap)):
        if not isinstance(value, (int, np.integer)) or isinstance(value, (bool, np.bool_)):
            raise ValueError(f"{name} must be an integer")
    if n_rows < 0 or train_size <= 0 or test_size <= 0 or gap < 0:
        raise ValueError("n_rows/gap must be nonnegative, train/test sizes positive")
    if step is None:
        step = test_size
    if not isinstance(step, (int, np.integer)) or isinstance(step, (bool, np.bool_)) or step < test_size:
        raise ValueError("step must be an integer >= test_size to avoid overlapping test returns")
    if not isinstance(expanding, bool):
        raise ValueError("expanding must be bool")

    test_start = train_size + gap
    while test_start + test_size <= n_rows:
        train_stop = test_start - gap
        train_start = 0 if expanding else train_stop - train_size
        yield WalkForwardWindow(train_start, train_stop, test_start, test_start + test_size)
        test_start += step


def return_statistics(daily_net_returns, benchmark_net_returns=None, periods_per_year=252):
    """Summarise strictly out-of-sample DAILY NET simple returns.

    Supply transaction costs and slippage in the daily return stream. Sharpe
    assumes a zero risk-free rate. Annualisation and sample size matter; this
    is an assessment tool, not a return forecast.
    """
    r = np.asarray(daily_net_returns, dtype=float)
    if r.ndim != 1 or not len(r) or not np.isfinite(r).all() or (r <= -1.0).any():
        raise ValueError("returns must be a nonempty finite 1-D sequence greater than -100%")
    if not isinstance(periods_per_year, (int, float)) or not np.isfinite(periods_per_year) or periods_per_year <= 0:
        raise ValueError("periods_per_year must be a positive finite number")
    e = np.r_[1.0, np.cumprod(1.0 + r)]
    peak = np.maximum.accumulate(e)
    sigma = float(np.std(r, ddof=1)) if len(r) > 1 else 0.0
    stats = {
        "days": int(len(r)),
        "total_return_pct": float((e[-1] - 1) * 100),
        "annualized_return_pct": float((e[-1] ** (periods_per_year / len(r)) - 1) * 100),
        "sharpe_zero_rf": float(np.mean(r) / sigma * np.sqrt(periods_per_year)) if sigma > 0 else 0.0,
        "max_drawdown_pct": float(np.min(e / peak - 1) * 100),
    }
    if benchmark_net_returns is not None:
        b = np.asarray(benchmark_net_returns, dtype=float)
        if b.shape != r.shape or not np.isfinite(b).all() or (b <= -1.0).any():
            raise ValueError("benchmark returns must have the same dates and valid returns")
        stats["benchmark_total_return_pct"] = float((np.prod(1 + b) - 1) * 100)
        stats["excess_total_return_pct"] = stats["total_return_pct"] - stats["benchmark_total_return_pct"]
    return stats


def block_bootstrap_drawdown(daily_net_returns, block_size=10, simulations=500, seed=42):
    """Resample contiguous return blocks to stress-test path-dependence.

    Preserves some local serial dependence, unlike independent daily shuffling.
    The lower-tail drawdown statistic is a scenario, not a confidence guarantee.
    """
    r = np.asarray(daily_net_returns, dtype=float)
    if r.ndim != 1 or not len(r) or not np.isfinite(r).all() or (r <= -1.0).any():
        raise ValueError("returns must be a nonempty finite 1-D sequence greater than -100%")
    if not isinstance(block_size, (int, np.integer)) or isinstance(block_size, (bool, np.bool_)) or block_size <= 0:
        raise ValueError("block_size must be positive integer")
    if not isinstance(simulations, (int, np.integer)) or isinstance(simulations, (bool, np.bool_)) or simulations <= 0:
        raise ValueError("simulations must be positive integer")
    rng = np.random.default_rng(seed)
    n = len(r)
    offsets = np.arange(min(block_size, n))
    out = np.empty(simulations, dtype=float)
    for i in range(simulations):
        starts = rng.integers(0, n, size=int(np.ceil(n / len(offsets))))
        sample = r[((starts[:, None] + offsets[None, :]) % n).ravel()[:n]]
        e = np.r_[1.0, np.cumprod(1 + sample)]
        out[i] = float(np.min(e / np.maximum.accumulate(e) - 1) * 100)
    return {"p05_drawdown_pct": float(np.percentile(out, 5)),
            "median_drawdown_pct": float(np.median(out)),
            "p95_drawdown_pct": float(np.percentile(out, 95))}
