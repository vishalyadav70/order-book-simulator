import asyncio
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text
from core.order_book import OrderBook
from analysis.fill_probability import FillProbabilityModel
from analysis.market_impact import MarketImpactModel

console = Console()

class LiveDashboard:
    def __init__(self, book: OrderBook,
                 fill_model: FillProbabilityModel,
                 impact_model: MarketImpactModel):
        self.book = book
        self.fill_model = fill_model
        self.impact_model = impact_model
        self.updates = 0
        self.start_time = time.time()

    def _order_book_table(self) -> Table:
        table = Table(
            title="Live BTC-USDT Order Book",
            show_header=True,
            header_style="bold",
            min_width=45
        )
        table.add_column("Ask Price", style="red", justify="right", min_width=10)
        table.add_column("Ask Qty", justify="right", min_width=8)
        table.add_column("Bid Price", style="green", justify="right", min_width=10)
        table.add_column("Bid Qty", justify="right", min_width=8)

        asks = list(self.book.asks.items())[:5]
        bids = list(self.book.bids.items())[:5]

        max_rows = max(len(asks), len(bids))
        for i in range(max_rows):
            ask_price = f"{asks[i][0]:,.1f}" if i < len(asks) else ""
            ask_qty = f"{sum(o.quantity for o in asks[i][1]):.4f}" if i < len(asks) else ""
            bid_price = f"{bids[i][0]:,.1f}" if i < len(bids) else ""
            bid_qty = f"{sum(o.quantity for o in bids[i][1]):.4f}" if i < len(bids) else ""
            table.add_row(ask_price, ask_qty, bid_price, bid_qty)

        return table

    def _stats_panel(self) -> Panel:
        spread = self.book.spread()
        best_bid = self.book.best_bid()
        best_ask = self.book.best_ask()
        elapsed = time.time() - self.start_time
        ups = self.updates / elapsed if elapsed > 0 else 0

        # Fill probability for 0.1 BTC at best bid
        fill_info = {}
        if best_bid:
            fill_info = self.fill_model.fill_probability(
                best_bid, "bid", 0.1)

        # Market impact for 1 BTC order
        impact_info = {}
        if best_ask:
            impact_info = self.impact_model.estimate_impact(1.0, "bid")

        text = Text()
        text.append("─── Price ───────────────\n", style="dim")
        text.append(f"Best Bid  : ", style="dim")
        text.append(f"{best_bid:>10,.1f}\n" if best_bid else "N/A\n", style="green bold")
        text.append(f"Best Ask  : ", style="dim")
        text.append(f"{best_ask:>10,.1f}\n" if best_ask else "N/A\n", style="red bold")
        text.append(f"Spread    : ", style="dim")
        text.append(f"{spread:>10,.1f}\n" if spread else "N/A\n", style="yellow")

        text.append("\n─── Feed ────────────────\n", style="dim")
        text.append(f"Updates/s : ", style="dim")
        text.append(f"{ups:>10.1f}\n", style="cyan")
        text.append(f"Total Upd : ", style="dim")
        text.append(f"{self.updates:>10,}\n", style="cyan")

        if fill_info:
            text.append("\n─── Fill Probability ────\n", style="dim")
            text.append(f"0.1 BTC @ best bid\n", style="dim")
            prob = fill_info['probability']
            color = "green" if prob > 0.7 else "yellow" if prob > 0.4 else "red"
            text.append(f"Probability: ", style="dim")
            text.append(f"{prob:.1%}\n", style=color)
            text.append(f"Qty Ahead : ", style="dim")
            text.append(f"{fill_info['qty_ahead']:.4f} BTC\n", style="dim")

        if impact_info:
            text.append("\n─── Market Impact (1 BTC) ─\n", style="dim")
            text.append(f"Impact bps : ", style="dim")
            text.append(f"{impact_info['impact_bps']:.2f}\n", style="yellow")
            text.append(f"Slippage  : ", style="dim")
            text.append(f"${impact_info['estimated_slippage_usd']:.2f}\n", style="yellow")

        return Panel(text, title="Market Stats", border_style="blue", width=32)

    def render(self):
        return Columns([
            self._order_book_table(),
            self._stats_panel()
        ])

    def increment(self):
        self.updates += 1