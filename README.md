# Live HFT Order Book Simulator

A high-performance, event-driven Limit Order Book (LOB) simulator with live Binance WebSocket feed, built in Python.

## Features

- **Live Data** — Real-time BTC-USDT order book from Binance WebSocket
- **Matching Engine** — Price-time priority matching (FIFO)
- **Fill Probability Model** — Queue position based fill estimation
- **Market Impact Model** — Square-root market impact + slippage estimation
- **Live Terminal Dashboard** — Real-time order book visualization using Rich
- **Benchmarked** — 100K+ events/sec on 1M order simulation

## Demo

```
Live BTC-USDT Order Book
┌─────────────┬──────────┬─────────────┬──────────┐
│  Ask Price  │  Ask Qty │   Bid Price │  Bid Qty │
├─────────────┼──────────┼─────────────┼──────────┤
│  76,681.3   │ 218.2758 │   76,681.3  │  97.3514 │
│  76,682.0   │   0.0528 │   76,681.2  │   0.0009 │
└─────────────┴──────────┴─────────────┴──────────┘

Market Stats
Best Bid  :   76,681.3
Best Ask  :   76,681.3
Spread    :        0.0
Updates/s :        9.4
```

## Project Structure

```
order_book_simulator/
├── core/
│   ├── order.py              # Order dataclass (Side, OrderType)
│   ├── order_book.py         # LOB engine with SortedDict
│   └── simulator.py          # Event-driven + FastSimulator
├── feed/
│   └── binance_ws.py         # Live Binance WebSocket feed
├── analysis/
│   ├── fill_probability.py   # Queue position fill model
│   └── market_impact.py      # Square-root market impact model
├── dashboard/
│   └── live_dashboard.py     # Rich terminal dashboard
├── benchmark/
│   └── bench.py              # 1M order benchmark
└── main.py                   # Entry point
```

## Installation

```bash
git clone https://github.com/vishalyadav70/order-book-simulator.git
cd order-book-simulator
pip install -r requirements.txt
```

## Usage

### Live Simulator
```bash
python main.py
```
Press `Ctrl+C` to stop.

### Benchmark
```bash
python benchmark/bench.py
```

## Technical Details

### Matching Engine
- Price-time priority (FIFO) matching
- O(log n) insert/delete using `SortedDict`
- Supports Limit, Market, and Cancel orders

### Fill Probability Model
- Exponential decay model based on queue position
- `P(fill) = exp(-λ * qty_ahead / avg_trade_size)`
- Price distance penalty applied

### Market Impact Model
- Square-root model (industry standard)
- `Impact = σ * sqrt(Q / ADV)`
- Real-time slippage estimation via book depth walk

### Performance
- 100K+ events/sec (pure Python)
- P99 latency < 50 microseconds
- Benchmarked on 1M order events

## Tech Stack

- `Python 3.11+`
- `sortedcontainers` — O(log n) order book
- `asyncio` — event-driven architecture
- `websockets` — Binance live feed
- `numpy` — latency analysis
- `rich` — terminal dashboard

## Requirements

```
sortedcontainers
numpy
websockets
rich
```
