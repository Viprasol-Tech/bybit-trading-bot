# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[SemVer](https://semver.org/).

## [0.2.0] - 2025

### Added
- **High-level Bybit v5 endpoint builders** on `BybitClient`: `get_kline`,
  `get_tickers`, `get_positions`, `get_wallet_balance`, `place_order`, and
  `cancel_order` — all returning fully-signed, ready-to-send `PreparedRequest`s.
- **Typed trading enumerations** (`Side`, `OrderType`, `TimeInForce`,
  `Category`, `Interval`) that mirror Bybit's exact wire casing.
- **Order types and time-in-force**: market/limit orders with `GTC`, `IOC`,
  `FOK`, and `PostOnly`, plus `orderLinkId` and `reduceOnly` support.
- **Paper backtester** (`run_backtest`) with an equity curve and performance
  metrics: total return, maximum drawdown, and an annualised Sharpe ratio.
- **SMA-crossover strategy** (`SmaCrossStrategy`) plus a reusable `sma` helper
  and a `Strategy` protocol.
- **Typed configuration** (`Settings`) with `BYBIT_*` environment loading,
  validation, and a `testnet`-aware `base_url`.
- **New CLI subcommands**: `order`, `kline`, `balance`, and `backtest`
  alongside the existing `demo` and `version`.

### Changed
- `BybitClient.place_order` now backs the `demo` command, replacing the
  hand-built order dictionary.
- Roughly quadrupled the test suite (86 tests) covering the new modules.

## [0.1.0] - 2025

### Added
- Initial release of bybit-trading-bot: Bybit API trading bot with HMAC-SHA256 v5 auth and paper trading.
