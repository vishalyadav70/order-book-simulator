import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rich.live import Live
from core.order_book import OrderBook
from feed.binance_ws import BinanceWebSocket
from analysis.fill_probability import FillProbabilityModel
from analysis.market_impact import MarketImpactModel
from dashboard.live_dashboard import LiveDashboard

async def main():
    # Setup
    book = OrderBook("BTC-USDT")
    fill_model = FillProbabilityModel(book)
    impact_model = MarketImpactModel(book)
    dashboard = LiveDashboard(book, fill_model, impact_model)
    ws = BinanceWebSocket("btcusdt")

    async def on_orders(orders):
        # Har live order process karo
        for order in orders:
            trades = book.add_order(order)
            for trade in trades:
                impact_model.record_trade(trade["price"], trade["qty"])
        dashboard.increment()

    # Live dashboard + WebSocket saath chalao
    with Live(dashboard.render(), refresh_per_second=4, screen=True) as live:
        async def update_display():
            while True:
                live.update(dashboard.render())
                await asyncio.sleep(0.25)

        await asyncio.gather(
            ws.stream(on_orders),
            update_display()
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulator band ho gaya!")