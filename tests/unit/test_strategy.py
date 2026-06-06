from __future__ import annotations

import pytest

from bybit_trading_bot.strategy import Signal, SmaCrossStrategy, sma


def test_sma_warmup_is_none() -> None:
    result = sma([1.0, 2.0, 3.0, 4.0], 3)
    assert result[0] is None
    assert result[1] is None
    assert result[2] == pytest.approx(2.0)
    assert result[3] == pytest.approx(3.0)


def test_sma_rolling_window() -> None:
    result = sma([10.0, 20.0, 30.0, 40.0, 50.0], 2)
    assert result == [None, 15.0, 25.0, 35.0, 45.0]


def test_sma_rejects_nonpositive_window() -> None:
    with pytest.raises(ValueError):
        sma([1.0, 2.0], 0)


def test_strategy_validates_windows() -> None:
    with pytest.raises(ValueError):
        SmaCrossStrategy(fast=30, slow=10)
    with pytest.raises(ValueError):
        SmaCrossStrategy(fast=0, slow=10)


def test_strategy_emits_one_signal_per_bar() -> None:
    closes = [float(x) for x in range(50)]
    signals = SmaCrossStrategy(fast=3, slow=5).generate(closes)
    assert len(signals) == len(closes)


def test_uptrend_goes_long() -> None:
    # A strictly rising series keeps the fast SMA above the slow SMA.
    closes = [float(x) for x in range(1, 41)]
    signals = SmaCrossStrategy(fast=3, slow=5).generate(closes)
    # Once both SMAs are defined, every later bar should be LONG.
    assert signals[-1] == Signal.LONG
    assert all(s == Signal.LONG for s in signals[6:])


def test_warmup_is_flat() -> None:
    closes = [float(x) for x in range(1, 41)]
    signals = SmaCrossStrategy(fast=3, slow=5).generate(closes)
    # Before the slow SMA is defined (index < 4) the signal must be FLAT.
    assert all(s == Signal.FLAT for s in signals[:4])


def test_downtrend_stays_flat() -> None:
    closes = [float(x) for x in range(40, 0, -1)]
    signals = SmaCrossStrategy(fast=3, slow=5).generate(closes)
    assert all(s == Signal.FLAT for s in signals)
