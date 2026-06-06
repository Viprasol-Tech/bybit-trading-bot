"""Signal-generating strategies for the paper backtester.

A strategy maps a stream of closing prices to a stream of discrete
:class:`Signal` values (long / flat). The bundled
:class:`SmaCrossStrategy` is a classic fast/slow moving-average crossover: go
long when the fast SMA is above the slow SMA, otherwise stay flat.

Strategies are pure and stateless across calls — they take the full price
history and return one signal per bar — which keeps them trivially testable and
deterministic for backtesting.

Part of Bybit Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum
from typing import Protocol


class Signal(IntEnum):
    """A discrete position signal for a single bar."""

    FLAT = 0
    LONG = 1


class Strategy(Protocol):
    """Protocol for any strategy usable by the backtester."""

    def generate(self, closes: Sequence[float]) -> list[Signal]:
        """Return one :class:`Signal` per input close price."""
        ...


def sma(values: Sequence[float], window: int) -> list[float | None]:
    """Compute a simple moving average over ``values``.

    Args:
        values: The input series (e.g. closing prices).
        window: Look-back length; must be a positive integer.

    Returns:
        A list the same length as ``values`` where the first ``window - 1``
        entries are ``None`` (insufficient history) and the rest hold the mean
        of the trailing ``window`` values.

    Raises:
        ValueError: If ``window`` is not positive.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    out: list[float | None] = []
    running = 0.0
    for i, value in enumerate(values):
        running += value
        if i >= window:
            running -= values[i - window]
        if i >= window - 1:
            out.append(running / window)
        else:
            out.append(None)
    return out


@dataclass(slots=True, frozen=True)
class SmaCrossStrategy:
    """Fast/slow simple-moving-average crossover strategy.

    Goes :attr:`Signal.LONG` whenever the fast SMA is strictly above the slow
    SMA and both are defined, otherwise :attr:`Signal.FLAT`.

    Attributes:
        fast: Fast (short) SMA window.
        slow: Slow (long) SMA window; must exceed ``fast``.
    """

    fast: int = 10
    slow: int = 30

    def __post_init__(self) -> None:
        if self.fast <= 0 or self.slow <= 0:
            raise ValueError("fast and slow windows must be positive")
        if self.fast >= self.slow:
            raise ValueError("fast window must be smaller than slow window")

    def generate(self, closes: Sequence[float]) -> list[Signal]:
        """Return long/flat signals for each bar in ``closes``.

        Args:
            closes: Closing prices in chronological order.

        Returns:
            A list of :class:`Signal` values, one per close.
        """
        fast_sma = sma(closes, self.fast)
        slow_sma = sma(closes, self.slow)
        signals: list[Signal] = []
        for f, s in zip(fast_sma, slow_sma, strict=True):
            if f is not None and s is not None and f > s:
                signals.append(Signal.LONG)
            else:
                signals.append(Signal.FLAT)
        return signals
