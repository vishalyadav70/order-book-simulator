import asyncio
import json
import websockets
from core.order import Order, Side, OrderType

class BinanceWebSocket:
    """
    Binance ka live order book data consume karta hai
    wss://stream.binance.com — free, no API key needed
    """
    def __init__(self, symbol: str = "btcusdt", depth: int = 20):
        self.symbol = symbol
        self.depth = depth
        # Binance diff depth stream — real time order book updates
        self.url = f"wss://stream.binance.com:9443/ws/{symbol}@depth@100ms"
        self.order_id_counter = 0
        self.running = False

    def _next_id(self) -> int:
        self.order_id_counter += 1
        return self.order_id_counter

    def _parse_orders(self, data: dict) -> list[Order]:
        """
        Binance depth update ko Order objects mein convert karo
        'b' = bids, 'a' = asks
        [price, quantity] format mein aata hai
        quantity = 0 matlab wo level remove ho gaya
        """
        orders = []

        for price_str, qty_str in data.get("b", []):
            price = float(price_str)
            qty = float(qty_str)
            if qty > 0:  # qty=0 means level removed
                orders.append(Order(
                    order_id=self._next_id(),
                    side=Side.BID,
                    price=price,
                    quantity=qty,
                    order_type=OrderType.LIMIT
                ))

        for price_str, qty_str in data.get("a", []):
            price = float(price_str)
            qty = float(qty_str)
            if qty > 0:
                orders.append(Order(
                    order_id=self._next_id(),
                    side=Side.ASK,
                    price=price,
                    quantity=qty,
                    order_type=OrderType.LIMIT
                ))

        return orders

    async def stream(self, callback):
        """
        Live stream chalu karo
        callback — har update pe call hoga
        """
        self.running = True
        print(f"Connecting to Binance WebSocket...")
        print(f"Symbol: {self.symbol.upper()}")

        async with websockets.connect(self.url) as ws:
            print(f"Connected! Live data aa raha hai...\n")
            while self.running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    data = json.loads(msg)
                    orders = self._parse_orders(data)
                    if orders:
                        await callback(orders)
                except asyncio.TimeoutError:
                    print("Timeout — reconnecting...")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break

    def stop(self):
        self.running = False