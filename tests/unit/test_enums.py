from __future__ import annotations

from bybit_trading_bot.enums import (
    Category,
    Interval,
    OrderType,
    Side,
    TimeInForce,
)


def test_side_wire_values() -> None:
    assert Side.BUY.value == "Buy"
    assert Side.SELL.value == "Sell"


def test_order_type_wire_values() -> None:
    assert OrderType.MARKET.value == "Market"
    assert OrderType.LIMIT.value == "Limit"


def test_time_in_force_wire_values() -> None:
    assert TimeInForce.GTC.value == "GTC"
    assert TimeInForce.IOC.value == "IOC"
    assert TimeInForce.FOK.value == "FOK"
    assert TimeInForce.POST_ONLY.value == "PostOnly"


def test_category_wire_values() -> None:
    assert {c.value for c in Category} == {"spot", "linear", "inverse", "option"}


def test_interval_minute_values_are_bare_numbers() -> None:
    assert Interval.M1.value == "1"
    assert Interval.H1.value == "60"
    assert Interval.H4.value == "240"


def test_interval_calendar_values() -> None:
    assert Interval.D1.value == "D"
    assert Interval.W1.value == "W"
    assert Interval.MN1.value == "M"


def test_enums_are_str_subclasses() -> None:
    assert isinstance(Side.BUY, str)
    assert Side.BUY == "Buy"
