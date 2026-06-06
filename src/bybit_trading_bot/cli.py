"""Command-line interface for Bybit Trading Bot.

Subcommands:

- ``version``  — print the installed version.
- ``demo``     — show signed ``X-BAPI-*`` headers and a paper round-trip.
- ``order``    — print a signed order request (no network I/O).
- ``kline``    — print a signed market kline request.
- ``balance``  — print a signed wallet-balance request.
- ``backtest`` — run an SMA-crossover backtest on synthetic prices and report
  metrics.

Everything here is offline and key-free: requests are *prepared and signed* but
never sent, so you can inspect exactly what would hit Bybit.

Part of Bybit Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math

import typer
from rich.console import Console
from rich.table import Table

from bybit_trading_bot import __version__
from bybit_trading_bot.backtest import run_backtest
from bybit_trading_bot.client import TESTNET_BASE_URL, BybitClient, PreparedRequest
from bybit_trading_bot.enums import Category, Interval, OrderType, Side, TimeInForce
from bybit_trading_bot.paper import PaperAccount
from bybit_trading_bot.strategy import SmaCrossStrategy

app = typer.Typer(add_completion=False, help="Bybit Trading Bot - by Viprasol Tech.")
console = Console()

#: A deterministic timestamp so demo output is reproducible.
_DEMO_TIMESTAMP = 1_700_000_000_000


def _demo_client() -> BybitClient:
    """Return a key-free client pointed at testnet for offline previews."""
    return BybitClient(
        api_key="demo-key",
        api_secret="demo-secret",
        base_url=TESTNET_BASE_URL,
    )


def _print_request(request: PreparedRequest) -> None:
    """Render a :class:`PreparedRequest` as a table plus method/URL/body."""
    table = Table(title="Signed Bybit v5 request headers")
    table.add_column("Header", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    for key in (
        "X-BAPI-API-KEY",
        "X-BAPI-TIMESTAMP",
        "X-BAPI-RECV-WINDOW",
        "X-BAPI-SIGN",
    ):
        table.add_row(key, request.headers[key])
    console.print(table)
    console.print(f"{request.method} {request.url}")
    if request.body is not None:
        console.print(f"Body: {request.body}")


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"bybit-trading-bot [bold cyan]{__version__}[/] - by Viprasol Tech")


@app.command()
def demo(
    symbol: str = typer.Option("BTCUSDT", help="Trading symbol for the demo."),
) -> None:
    """Show signed Bybit v5 headers and run a paper-trading round-trip."""
    client = _demo_client()
    request = client.place_order(
        symbol,
        Side.BUY,
        OrderType.MARKET,
        "0.001",
        category=Category.SPOT,
        timestamp=_DEMO_TIMESTAMP,
    )
    _print_request(request)
    console.print()

    account = PaperAccount(cash=10_000.0)
    buy_price = 30_000.0
    sell_price = 31_500.0
    account.buy(symbol, 0.1, buy_price)
    console.print(
        f"BUY  0.1 {symbol} @ {buy_price:,.2f} -> cash ${account.cash:,.2f}, "
        f"position {account.position(symbol)}"
    )
    account.sell(symbol, 0.1, sell_price)
    console.print(
        f"SELL 0.1 {symbol} @ {sell_price:,.2f} -> cash ${account.cash:,.2f}, "
        f"position {account.position(symbol)}"
    )

    final = account.equity({symbol: sell_price})
    console.print(f"\nFinal equity: [bold green]${final:,.2f}[/] (started $10,000.00)")


@app.command()
def order(
    symbol: str = typer.Option("BTCUSDT", help="Trading symbol."),
    side: Side = typer.Option(Side.BUY, help="Order side."),
    order_type: OrderType = typer.Option(OrderType.LIMIT, help="Order type."),
    qty: str = typer.Option("0.001", help="Order quantity."),
    price: str | None = typer.Option(None, help="Limit price (required for Limit)."),
    tif: TimeInForce = typer.Option(TimeInForce.GTC, help="Time in force."),
) -> None:
    """Print a signed order request without sending it."""
    client = _demo_client()
    request = client.place_order(
        symbol,
        side,
        order_type,
        qty,
        category=Category.SPOT,
        price=price,
        time_in_force=tif,
        timestamp=_DEMO_TIMESTAMP,
    )
    _print_request(request)


@app.command()
def kline(
    symbol: str = typer.Option("BTCUSDT", help="Trading symbol."),
    interval: Interval = typer.Option(Interval.H1, help="Candle interval."),
    limit: int = typer.Option(200, min=1, max=1000, help="Number of candles."),
) -> None:
    """Print a signed market-kline request without sending it."""
    client = _demo_client()
    request = client.get_kline(
        symbol,
        interval,
        category=Category.SPOT,
        limit=limit,
        timestamp=_DEMO_TIMESTAMP,
    )
    _print_request(request)


@app.command()
def balance(
    account_type: str = typer.Option("UNIFIED", help="Account type."),
    coin: str | None = typer.Option(None, help="Optional coin filter."),
) -> None:
    """Print a signed wallet-balance request without sending it."""
    client = _demo_client()
    request = client.get_wallet_balance(
        account_type=account_type,
        coin=coin,
        timestamp=_DEMO_TIMESTAMP,
    )
    _print_request(request)


@app.command()
def backtest(
    fast: int = typer.Option(10, min=1, help="Fast SMA window."),
    slow: int = typer.Option(30, min=2, help="Slow SMA window."),
    bars: int = typer.Option(300, min=10, help="Number of synthetic price bars."),
    cash: float = typer.Option(10_000.0, min=1.0, help="Starting cash."),
    fee_rate: float = typer.Option(0.001, min=0.0, help="Per-fill fee rate."),
) -> None:
    """Backtest an SMA crossover on a deterministic synthetic price series."""
    closes = _synthetic_prices(bars)
    strategy = SmaCrossStrategy(fast=fast, slow=slow)
    result = run_backtest(closes, strategy, starting_cash=cash, fee_rate=fee_rate)

    table = Table(title=f"SMA({fast}/{slow}) backtest over {bars} bars")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="white", justify="right")
    table.add_row("Trades", str(result.trades))
    table.add_row("Starting equity", f"${result.starting_equity:,.2f}")
    table.add_row("Final equity", f"${result.final_equity:,.2f}")
    table.add_row("Total return", f"{result.total_return * 100:,.2f}%")
    table.add_row("Max drawdown", f"{result.max_drawdown * 100:,.2f}%")
    table.add_row("Sharpe (ann.)", f"{result.sharpe():.2f}")
    console.print(table)


def _synthetic_prices(bars: int) -> list[float]:
    """Generate a deterministic, trend-plus-cycle price series.

    Args:
        bars: Number of price points to generate.

    Returns:
        A reproducible list of positive closing prices.
    """
    base = 30_000.0
    return [base * (1.0 + 0.0006 * i + 0.04 * math.sin(i / 9.0)) for i in range(bars)]


if __name__ == "__main__":
    app()
