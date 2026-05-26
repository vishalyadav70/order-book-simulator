import numpy as np
from collections import deque
from core.order_book import OrderBook

class MarketImpactModel:
    """
    Order size ke basis pe price impact estimate karta hai
    
    Square root model use karta hai — industry standard:
    Impact = sigma * sqrt(Q / ADV)
    
    sigma = volatility
    Q = order size
    ADV = average daily volume
    """
    def __init__(self, book: OrderBook, adv: float = 1000.0):
        self.book = book
        self.adv = adv          # Average Daily Volume (BTC)
        self.trade_history = deque(maxlen=1000)  # last 1000 trades
        self.price_history = deque(maxlen=500)   # last 500 prices

    def volatility(self) -> float:
        """
        Recent price history se volatility calculate karo
        """
        if len(self.price_history) < 10:
            return 0.001  # default 0.1%
        prices = np.array(self.price_history)
        returns = np.diff(np.log(prices))
        return float(np.std(returns))

    def estimate_impact(self, quantity: float, side: str) -> dict:
        """
        Ek order ke price impact ka estimate

        Returns:
        - expected_impact: kitna price move hoga (%)
        - implementation_shortfall: expected vs actual price diff
        - market_impact_bps: basis points mein impact
        """
        sigma = self.volatility()

        # Square root market impact model
        # Impact = sigma * sqrt(Q/ADV)
        impact_pct = sigma * np.sqrt(quantity / self.adv)

        best = self.book.best_ask() if side == "bid" else self.book.best_bid()
        if best is None:
            return {}

        impact_price = best * impact_pct
        impact_bps = impact_pct * 10000  # basis points

        # Slippage estimate — book depth se
        slippage = self._estimate_slippage(quantity, side)

        return {
            "quantity": quantity,
            "side": side,
            "expected_impact_pct": round(impact_pct * 100, 4),
            "impact_price_usd": round(impact_price, 2),
            "impact_bps": round(impact_bps, 2),
            "estimated_slippage_usd": round(slippage, 2),
            "volatility": round(sigma, 6),
        }

    def _estimate_slippage(self, quantity: float, side: str) -> float:
        """
        Book depth walk karke actual slippage estimate karo
        """
        book = self.book.asks if side == "bid" else self.book.bids
        if not book:
            return 0.0

        remaining = quantity
        cost = 0.0
        best_price = next(iter(book))

        for price, queue in book.items():
            if remaining <= 0:
                break
            level_qty = sum(o.quantity for o in queue)
            fill_qty = min(remaining, level_qty)
            cost += fill_qty * (price - best_price)
            remaining -= fill_qty

        return cost

    def record_trade(self, price: float, quantity: float):
        """Trade history update karo"""
        self.trade_history.append({"price": price, "qty": quantity})
        self.price_history.append(price)