"""A deterministic paper backtester with performance metrics.

:func:`run_backtest` feeds a strategy's signals through a :class:`PaperAccount`,
entering a full-size long when the signal turns long and flattening when it turns
flat. It executes at the bar's close price, optionally charging a proportional
fee per fill, and records the equity curve so that risk/return metrics can be
computed.

The maths is intentionally simple and dependency-light (standard library only)
so results are fully reproducible and easy to reason about.

Part of Bybit Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass

from bybit_trading_bot.paper import PaperAccount
from bybit_trading_bot.strategy import Signal, Strategy


@dataclass(slots=True, frozen=True)
class BacktestResult:
    """The outcome of a backtest run.

    Attributes:
        equity_curve: Mark-to-market equity after each bar.
        trades: Number of fills executed (entries + exits).
        starting_equity: Equity before the first bar.
        final_equity: Equity after the last bar.
    """

    equity_curve: list[float]
    trades: int
    starting_equity: float
    final_equity: float

    @property
    def total_return(self) -> float:
        """Total return as a fraction (``0.1`` == +10%)."""
        if self.starting_equity == 0.0:
            return 0.0
        return self.final_equity / self.starting_equity - 1.0

    @property
    def max_drawdown(self) -> float:
        """Largest peak-to-trough equity decline as a positive fraction."""
        return max_drawdown(self.equity_curve)

    def sharpe(self, *, periods_per_year: int = 365) -> float:
        """Annualised Sharpe ratio of the equity curve's bar returns.

        Args:
            periods_per_year: Bars per year used to annualise (365 for daily).

        Returns:
            The annualised Sharpe ratio, or ``0.0`` if it is undefined.
        """
        return sharpe_ratio(self.equity_curve, periods_per_year=periods_per_year)


def bar_returns(equity_curve: Sequence[float]) -> list[float]:
    """Compute simple per-bar returns from an equity curve.

    Args:
        equity_curve: Equity values in chronological order.

    Returns:
        A list of ``len(equity_curve) - 1`` fractional returns; empty when the
        curve has fewer than two points.
    """
    returns: list[float] = []
    for prev, cur in itertools.pairwise(equity_curve):
        if prev == 0.0:
            returns.append(0.0)
        else:
            returns.append(cur / prev - 1.0)
    return returns


def max_drawdown(equity_curve: Sequence[float]) -> float:
    """Return the maximum drawdown of an equity curve.

    Args:
        equity_curve: Equity values in chronological order.

    Returns:
        The worst peak-to-trough decline as a positive fraction (``0.2`` ==
        a 20% drawdown); ``0.0`` for an empty or never-declining curve.
    """
    peak = -math.inf
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0.0:
            drawdown = (peak - value) / peak
            worst = max(worst, drawdown)
    return worst


def sharpe_ratio(
    equity_curve: Sequence[float],
    *,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 365,
) -> float:
    """Compute the annualised Sharpe ratio of an equity curve.

    Args:
        equity_curve: Equity values in chronological order.
        risk_free_rate: Per-bar risk-free return to subtract (default ``0``).
        periods_per_year: Bars per year used to annualise.

    Returns:
        The annualised Sharpe ratio, or ``0.0`` when volatility is zero or
        there are too few points to estimate it.
    """
    returns = bar_returns(equity_curve)
    if len(returns) < 2:
        return 0.0
    excess = [r - risk_free_rate for r in returns]
    mean = sum(excess) / len(excess)
    variance = sum((r - mean) ** 2 for r in excess) / (len(excess) - 1)
    std = math.sqrt(variance)
    if std == 0.0:
        return 0.0
    return (mean / std) * math.sqrt(periods_per_year)


def run_backtest(
    closes: Sequence[float],
    strategy: Strategy,
    *,
    symbol: str = "BTCUSDT",
    starting_cash: float = 10_000.0,
    fee_rate: float = 0.0,
) -> BacktestResult:
    """Run ``strategy`` over ``closes`` against a fresh paper account.

    On each bar the strategy's signal is realised: a long signal with no open
    position buys the largest whole position the cash affords; a flat signal
    with an open position sells it. Fills happen at the bar's close and incur a
    proportional ``fee_rate``.

    Args:
        closes: Closing prices in chronological order.
        strategy: A :class:`~.strategy.Strategy` producing one signal per bar.
        symbol: Symbol traded inside the paper account.
        starting_cash: Opening quote-currency balance.
        fee_rate: Proportional fee per fill (``0.001`` == 0.1%).

    Returns:
        A :class:`BacktestResult` with the equity curve and trade count.

    Raises:
        ValueError: If ``fee_rate`` is negative or ``starting_cash`` is not
            positive.
    """
    if fee_rate < 0.0:
        raise ValueError("fee_rate must be non-negative")
    if starting_cash <= 0.0:
        raise ValueError("starting_cash must be positive")

    account = PaperAccount(cash=starting_cash)
    signals = strategy.generate(closes)
    equity_curve: list[float] = []
    trades = 0

    for price, signal in zip(closes, signals, strict=True):
        held = account.position(symbol)
        if signal == Signal.LONG and held == 0.0:
            budget = account.cash / (1.0 + fee_rate)
            qty = budget / price
            if qty > 0.0:
                account.buy(symbol, qty, price)
                account.cash -= qty * price * fee_rate
                trades += 1
        elif signal == Signal.FLAT and held > 0.0:
            account.sell(symbol, held, price)
            account.cash -= held * price * fee_rate
            trades += 1
        equity_curve.append(account.equity({symbol: price}))

    final = equity_curve[-1] if equity_curve else starting_cash
    return BacktestResult(
        equity_curve=equity_curve,
        trades=trades,
        starting_equity=starting_cash,
        final_equity=final,
    )
