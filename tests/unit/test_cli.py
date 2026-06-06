from __future__ import annotations

from typer.testing import CliRunner

from bybit_trading_bot import __version__
from bybit_trading_bot.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_demo_command_runs() -> None:
    result = runner.invoke(app, ["demo", "--symbol", "ETHUSDT"])
    assert result.exit_code == 0
    assert "X-BAPI-SIGN" in result.stdout
    assert "Final equity" in result.stdout


def test_order_command_limit() -> None:
    result = runner.invoke(
        app,
        ["order", "--order-type", "Limit", "--price", "30000", "--qty", "0.01"],
    )
    assert result.exit_code == 0
    assert "POST" in result.stdout
    assert "/v5/order/create" in result.stdout


def test_kline_command() -> None:
    result = runner.invoke(app, ["kline", "--interval", "60", "--limit", "50"])
    assert result.exit_code == 0
    assert "/v5/market/kline" in result.stdout


def test_balance_command() -> None:
    result = runner.invoke(app, ["balance", "--coin", "USDT"])
    assert result.exit_code == 0
    assert "/v5/account/wallet-balance" in result.stdout


def test_backtest_command_reports_metrics() -> None:
    result = runner.invoke(app, ["backtest", "--bars", "120", "--fast", "5", "--slow", "20"])
    assert result.exit_code == 0
    assert "Sharpe" in result.stdout
    assert "Max drawdown" in result.stdout
    assert "Total return" in result.stdout
