from __future__ import annotations

import math

import pytest

from bybit_trading_bot.backtest import (
    BacktestResult,
    bar_returns,
    max_drawdown,
    run_backtest,
    sharpe_ratio,
)
from bybit_trading_bot.strategy import Signal, SmaCrossStrategy, Strategy


class _AlwaysLong:
    """A fixture strategy that is long on every bar."""

    def generate(self, closes) -> list[Signal]:  # type: ignore[no-untyped-def]
        return [Signal.LONG for _ in closes]


class _AlwaysFlat:
    """A fixture strategy that never enters."""

    def generate(self, closes) -> list[Signal]:  # type: ignore[no-untyped-def]
        return [Signal.FLAT for _ in closes]


def test_bar_returns_simple() -> None:
    assert bar_returns([100.0, 110.0, 99.0]) == pytest.approx([0.1, -0.1])


def test_bar_returns_too_short() -> None:
    assert bar_returns([100.0]) == []


def test_max_drawdown_basic() -> None:
    # Peak 120 then trough 90 => (120-90)/120 = 0.25.
    assert max_drawdown([100.0, 120.0, 90.0, 110.0]) == pytest.approx(0.25)


def test_max_drawdown_monotonic_is_zero() -> None:
    assert max_drawdown([100.0, 110.0, 120.0]) == 0.0


def test_sharpe_zero_volatility() -> None:
    assert sharpe_ratio([100.0, 100.0, 100.0]) == 0.0


def test_sharpe_positive_for_steady_growth() -> None:
    curve = [100.0 * (1.01**i) for i in range(20)]
    # Constant positive return => zero std of excess => Sharpe is 0 by convention.
    # Add tiny noise to make volatility non-zero and the ratio positive.
    curve = [c * (1.0 + 0.0001 * (i % 2)) for i, c in enumerate(curve)]
    assert sharpe_ratio(curve) > 0.0


def test_always_flat_keeps_starting_equity() -> None:
    closes = [100.0, 105.0, 95.0, 110.0]
    result = run_backtest(closes, _AlwaysFlat(), starting_cash=1_000.0)
    assert result.trades == 0
    assert result.final_equity == pytest.approx(1_000.0)
    assert result.total_return == pytest.approx(0.0)


def test_always_long_tracks_price_no_fees() -> None:
    closes = [100.0, 200.0]
    result = run_backtest(closes, _AlwaysLong(), starting_cash=1_000.0, fee_rate=0.0)
    # Buy 10 units at 100, mark at 200 => equity 2000.
    assert result.trades == 1
    assert result.final_equity == pytest.approx(2_000.0)
    assert result.total_return == pytest.approx(1.0)


def test_fees_reduce_equity() -> None:
    closes = [100.0, 100.0]
    no_fee = run_backtest(closes, _AlwaysLong(), starting_cash=1_000.0, fee_rate=0.0)
    with_fee = run_backtest(closes, _AlwaysLong(), starting_cash=1_000.0, fee_rate=0.01)
    assert with_fee.final_equity < no_fee.final_equity


def test_round_trip_realises_profit() -> None:
    # Long on bar 1, flat on bar 2 -> sells the position into the rally.
    class _LongThenFlat:
        def generate(self, closes):  # type: ignore[no-untyped-def]
            return [Signal.LONG, Signal.FLAT]

    closes = [100.0, 150.0]
    result = run_backtest(closes, _LongThenFlat(), starting_cash=1_000.0)
    assert result.trades == 2
    assert result.final_equity == pytest.approx(1_500.0)


def test_run_backtest_validates_inputs() -> None:
    with pytest.raises(ValueError):
        run_backtest([100.0], _AlwaysLong(), fee_rate=-0.1)
    with pytest.raises(ValueError):
        run_backtest([100.0], _AlwaysLong(), starting_cash=0.0)


def test_result_metrics_consistent() -> None:
    closes = [30_000.0 * (1.0 + 0.0006 * i + 0.04 * math.sin(i / 9.0)) for i in range(200)]
    strategy: Strategy = SmaCrossStrategy(fast=10, slow=30)
    result = run_backtest(closes, strategy, fee_rate=0.001)
    assert isinstance(result, BacktestResult)
    assert len(result.equity_curve) == len(closes)
    assert result.max_drawdown >= 0.0
    assert result.starting_equity == pytest.approx(10_000.0)
    assert result.final_equity == pytest.approx(result.equity_curve[-1])
