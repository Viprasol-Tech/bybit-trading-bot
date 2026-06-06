"""Bybit v5 trading enumerations.

These string enumerations mirror the exact casing Bybit's v5 REST API expects in
request bodies (e.g. ``"Buy"``, ``"Market"``, ``"GTC"``). Using them instead of
raw strings keeps order construction type-safe and self-documenting.

Part of Bybit Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from enum import Enum


class Side(str, Enum):
    """Order side as sent in ``side``."""

    BUY = "Buy"
    SELL = "Sell"


class OrderType(str, Enum):
    """Order type as sent in ``orderType``."""

    MARKET = "Market"
    LIMIT = "Limit"


class TimeInForce(str, Enum):
    """Time-in-force policy as sent in ``timeInForce``.

    - ``GTC``: Good-Till-Cancelled.
    - ``IOC``: Immediate-Or-Cancel.
    - ``FOK``: Fill-Or-Kill.
    - ``POST_ONLY``: Maker-only; rejected if it would take liquidity.
    """

    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    POST_ONLY = "PostOnly"


class Category(str, Enum):
    """Product category as sent in ``category``."""

    SPOT = "spot"
    LINEAR = "linear"
    INVERSE = "inverse"
    OPTION = "option"


class Interval(str, Enum):
    """Kline (candlestick) interval as sent in ``interval``.

    Minute intervals are bare numbers; ``D``/``W``/``M`` are day/week/month.
    """

    M1 = "1"
    M3 = "3"
    M5 = "5"
    M15 = "15"
    M30 = "30"
    H1 = "60"
    H2 = "120"
    H4 = "240"
    H6 = "360"
    H12 = "720"
    D1 = "D"
    W1 = "W"
    MN1 = "M"
