from __future__ import annotations

import pytest

from bybit_trading_bot.paper import (
    InsufficientFundsError,
    InsufficientPositionError,
    PaperAccount,
)


def test_buy_debits_cash_and_adds_position() -> None:
    acct = PaperAccount(cash=10_000.0)
    cost = acct.buy("BTCUSDT", 0.1, 30_000.0)
    assert cost == 3_000.0
    assert acct.cash == 7_000.0
    assert acct.position("BTCUSDT") == pytest.approx(0.1)


def test_sell_credits_cash_and_reduces_position() -> None:
    acct = PaperAccount(cash=10_000.0)
    acct.buy("BTCUSDT", 0.1, 30_000.0)
    proceeds = acct.sell("BTCUSDT", 0.1, 31_500.0)
    assert proceeds == 3_150.0
    assert acct.cash == pytest.approx(10_150.0)
    assert acct.position("BTCUSDT") == 0.0
    assert "BTCUSDT" not in acct.positions


def test_partial_sell_keeps_remainder() -> None:
    acct = PaperAccount(cash=10_000.0)
    acct.buy("BTCUSDT", 0.2, 30_000.0)
    acct.sell("BTCUSDT", 0.05, 32_000.0)
    assert acct.position("BTCUSDT") == pytest.approx(0.15)


def test_round_trip_profit_math() -> None:
    acct = PaperAccount(cash=10_000.0)
    acct.buy("BTCUSDT", 0.1, 30_000.0)
    acct.sell("BTCUSDT", 0.1, 31_500.0)
    # Bought for 3000, sold for 3150 => +150 net.
    assert acct.cash == pytest.approx(10_150.0)
    assert acct.equity({"BTCUSDT": 31_500.0}) == pytest.approx(10_150.0)


def test_equity_marks_open_position_to_market() -> None:
    acct = PaperAccount(cash=7_000.0, positions={"BTCUSDT": 0.1})
    assert acct.equity({"BTCUSDT": 32_000.0}) == pytest.approx(10_200.0)


def test_buy_rejects_insufficient_funds() -> None:
    acct = PaperAccount(cash=100.0)
    with pytest.raises(InsufficientFundsError):
        acct.buy("BTCUSDT", 1.0, 30_000.0)
    assert acct.cash == 100.0


def test_sell_rejects_oversized_position() -> None:
    acct = PaperAccount(cash=10_000.0)
    acct.buy("BTCUSDT", 0.1, 30_000.0)
    with pytest.raises(InsufficientPositionError):
        acct.sell("BTCUSDT", 0.2, 31_000.0)


@pytest.mark.parametrize("qty,price", [(0.0, 100.0), (-1.0, 100.0), (1.0, 0.0), (1.0, -5.0)])
def test_invalid_inputs_raise_value_error(qty: float, price: float) -> None:
    acct = PaperAccount(cash=10_000.0)
    with pytest.raises(ValueError):
        acct.buy("BTCUSDT", qty, price)
