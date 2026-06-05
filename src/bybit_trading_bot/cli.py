"""Command-line interface for Bybit Trading Bot.

``bybit-trading-bot demo`` shows the signed ``X-BAPI-*`` headers for a sample
order request and runs a short sequence of paper trades — no API keys, no risk.

Part of Bybit Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from bybit_trading_bot import __version__
from bybit_trading_bot.client import TESTNET_BASE_URL, BybitClient
from bybit_trading_bot.paper import PaperAccount

app = typer.Typer(add_completion=False, help="Bybit Trading Bot — by Viprasol Tech.")
console = Console()

#: A deterministic timestamp so demo output is reproducible.
_DEMO_TIMESTAMP = 1_700_000_000_000


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"bybit-trading-bot [bold cyan]{__version__}[/] - by Viprasol Tech")


@app.command()
def demo(
    symbol: str = typer.Option("BTCUSDT", help="Trading symbol for the demo."),
) -> None:
    """Show signed Bybit v5 headers and run a paper-trading round-trip."""
    client = BybitClient(
        api_key="demo-key",
        api_secret="demo-secret",
        base_url=TESTNET_BASE_URL,
    )
    order = {
        "category": "spot",
        "symbol": symbol,
        "side": "Buy",
        "orderType": "Market",
        "qty": "0.001",
    }
    request = client.prepare_post("/v5/order/create", order, timestamp=_DEMO_TIMESTAMP)

    header_table = Table(title="Signed Bybit v5 request headers")
    header_table.add_column("Header", style="cyan", no_wrap=True)
    header_table.add_column("Value", style="white")
    for key in (
        "X-BAPI-API-KEY",
        "X-BAPI-TIMESTAMP",
        "X-BAPI-RECV-WINDOW",
        "X-BAPI-SIGN",
    ):
        header_table.add_row(key, request.headers[key])
    console.print(header_table)
    console.print(f"POST {request.url}")
    console.print(f"Body: {request.body}\n")

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


if __name__ == "__main__":
    app()
