"""Bybit Trading Bot — Bybit v5 HMAC auth, strategies and paper trading by Viprasol Tech."""

from __future__ import annotations

from bybit_trading_bot.auth import auth_headers, sign
from bybit_trading_bot.backtest import BacktestResult, run_backtest
from bybit_trading_bot.client import BybitClient, PreparedRequest
from bybit_trading_bot.config import Settings
from bybit_trading_bot.enums import (
    Category,
    Interval,
    OrderType,
    Side,
    TimeInForce,
)
from bybit_trading_bot.paper import PaperAccount
from bybit_trading_bot.strategy import Signal, SmaCrossStrategy

__version__ = "0.2.0"
__author__ = "Viprasol Tech Private Limited"
__all__ = [
    "BacktestResult",
    "BybitClient",
    "Category",
    "Interval",
    "OrderType",
    "PaperAccount",
    "PreparedRequest",
    "Settings",
    "Side",
    "Signal",
    "SmaCrossStrategy",
    "TimeInForce",
    "__version__",
    "auth_headers",
    "run_backtest",
    "sign",
]
