"""A minimal paper-trading account for risk-free simulation.

``PaperAccount`` tracks quote-currency cash and per-symbol positions, executing
buys and sells at a caller-supplied price. It performs no network I/O and is the
safe sandbox the CLI demo trades against.

Part of Bybit Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from dataclasses import dataclass, field


class InsufficientFundsError(Exception):
    """Raised when a buy would overdraw the available cash balance."""


class InsufficientPositionError(Exception):
    """Raised when a sell exceeds the held quantity for a symbol."""


@dataclass(slots=True)
class PaperAccount:
    """A simulated trading account holding cash and long positions.

    Args:
        cash: Starting quote-currency balance (e.g. USDT).
        positions: Optional opening positions as ``{symbol: quantity}``.

    Attributes:
        cash: Current quote-currency balance.
        positions: Held base-asset quantities keyed by symbol.
    """

    cash: float
    positions: dict[str, float] = field(default_factory=dict)

    def position(self, symbol: str) -> float:
        """Return the held quantity for ``symbol`` (``0.0`` if none).

        Args:
            symbol: The trading symbol, e.g. ``"BTCUSDT"``.

        Returns:
            The currently held base-asset quantity.
        """
        return self.positions.get(symbol, 0.0)

    def buy(self, symbol: str, quantity: float, price: float) -> float:
        """Buy ``quantity`` of ``symbol`` at ``price``, paying from cash.

        Args:
            symbol: The trading symbol, e.g. ``"BTCUSDT"``.
            quantity: Base-asset amount to buy; must be positive.
            price: Execution price per unit; must be positive.

        Returns:
            The total cost debited from cash.

        Raises:
            ValueError: If ``quantity`` or ``price`` is not positive.
            InsufficientFundsError: If cash cannot cover the cost.
        """
        _require_positive(quantity, price)
        cost = quantity * price
        if cost > self.cash:
            raise InsufficientFundsError(f"need {cost:.2f} but only {self.cash:.2f} cash available")
        self.cash -= cost
        self.positions[symbol] = self.position(symbol) + quantity
        return cost

    def sell(self, symbol: str, quantity: float, price: float) -> float:
        """Sell ``quantity`` of ``symbol`` at ``price``, crediting cash.

        Args:
            symbol: The trading symbol, e.g. ``"BTCUSDT"``.
            quantity: Base-asset amount to sell; must be positive.
            price: Execution price per unit; must be positive.

        Returns:
            The total proceeds credited to cash.

        Raises:
            ValueError: If ``quantity`` or ``price`` is not positive.
            InsufficientPositionError: If the held quantity is too small.
        """
        _require_positive(quantity, price)
        held = self.position(symbol)
        if quantity > held:
            raise InsufficientPositionError(f"cannot sell {quantity} {symbol}; only {held} held")
        proceeds = quantity * price
        self.cash += proceeds
        remaining = held - quantity
        if remaining == 0.0:
            self.positions.pop(symbol, None)
        else:
            self.positions[symbol] = remaining
        return proceeds

    def equity(self, prices: dict[str, float]) -> float:
        """Return total account value: cash plus marked-to-market positions.

        Args:
            prices: Current price per held symbol. Symbols missing from this
                map are valued at zero.

        Returns:
            The mark-to-market equity.
        """
        market_value = sum(qty * prices.get(symbol, 0.0) for symbol, qty in self.positions.items())
        return self.cash + market_value


def _require_positive(quantity: float, price: float) -> None:
    """Validate that ``quantity`` and ``price`` are strictly positive.

    Args:
        quantity: Order quantity to check.
        price: Order price to check.

    Raises:
        ValueError: If either value is not greater than zero.
    """
    if quantity <= 0.0:
        raise ValueError("quantity must be positive")
    if price <= 0.0:
        raise ValueError("price must be positive")
