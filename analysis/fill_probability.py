import numpy as np
from core.order_book import OrderBook

class FillProbabilityModel:
    """
    Queue position ke basis pe fill probability calculate karta hai
    
    Logic:
    - Agar tera order top of queue hai → high fill probability
    - Agar bohot orders pehle hain → low fill probability
    - Time decay bhi consider karta hai
    """
    def __init__(self, book: OrderBook):
        self.book = book
        self.fill_history = []  # past fills track karo

    def queue_position(self, price: float, side: str) -> tuple[int, float]:
        """
        Ek price level pe kitni quantity pehle hai
        Returns: (orders_ahead, quantity_ahead)
        """
        book = self.book.bids if side == "bid" else self.book.asks

        if price not in book:
            return 0, 0.0

        queue = book[price]
        orders_ahead = len(queue)
        qty_ahead = sum(o.quantity for o in queue)
        return orders_ahead, qty_ahead

    def fill_probability(self, price: float, side: str, 
                        quantity: float) -> dict:
        """
        Fill probability estimate karo

        Model:
        P(fill) = exp(-lambda * qty_ahead / avg_trade_size)
        lambda = decay factor (0.5 standard)
        """
        orders_ahead, qty_ahead = self.queue_position(price, side)

        # Best bid/ask se kitna door hai
        best = self.book.best_bid() if side == "bid" else self.book.best_ask()
        if best is None:
            return {"probability": 0.0, "qty_ahead": 0, "orders_ahead": 0}

        price_distance = abs(price - best)

        # Exponential decay model
        lambda_decay = 0.5
        avg_trade_size = 0.1  # BTC mein average trade

        if qty_ahead == 0:
            base_prob = 0.95  # top of queue
        else:
            base_prob = np.exp(-lambda_decay * qty_ahead / avg_trade_size)

        # Price distance se adjust karo
        # Zyada door = kam probability
        distance_penalty = np.exp(-price_distance / 100)
        final_prob = base_prob * distance_penalty

        return {
            "probability": round(float(final_prob), 4),
            "qty_ahead": round(qty_ahead, 4),
            "orders_ahead": orders_ahead,
            "price_distance": round(price_distance, 2),
            "base_prob": round(float(base_prob), 4)
        }