#LOB engine (main)

from sortedcontainers import SortedDict
from collections import deque
from core.order import Order, Side, OrderType

class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        
        # Bids — highest price pehle chahiye
        # isliye negative key trick use ki (SortedDict ascending order mein sort karta hai)
        # -30100 < -30000, toh 30100 pehle aayega ✓
        
        self.bids: SortedDict = SortedDict(lambda x: -x)
        
        # Asks — lowest price pehle chahiye (default ascending = sahi hai)
        self.asks: SortedDict = SortedDict()
        
        # order_id → Order mapping — fast cancel ke liye
        # O(1) lookup by order_id
        self.orders: dict[int, Order] = {}

    def _add_to_book(self, order: Order):
        # BID hai toh bids mein, ASK hai toh asks mein daalo
        book = self.bids if order.side == Side.BID else self.asks
        
        # Agar yeh price level pehle se exist nahi karta
        # toh ek naya deque (queue) banao us price ke liye
        # deque isliye — O(1) left pop (FIFO = price-time priority)
        if order.price not in book:
            book[order.price] = deque()
        
        # Order queue mein daalo aur orders dict mein bhi
        book[order.price].append(order)
        self.orders[order.order_id] = order

    def _cancel(self, order_id: int):
        # Order exist karta hai?
        if order_id not in self.orders:
            return
        
        order = self.orders[order_id]
        book = self.bids if order.side == Side.BID else self.asks
        
        # Queue se remove karo
        if order.price in book:
            book[order.price].remove(order)
            # Agar us price pe koi order nahi bacha toh
            # price level hi hata do
            if not book[order.price]:
                del book[order.price]
        
        # orders dict se bhi hata do
        del self.orders[order_id]

    def best_bid(self):
        # Sabse upar wala bid price
        return next(iter(self.bids)) if self.bids else None

    def best_ask(self):
        # Sabse kam wala ask price
        return next(iter(self.asks)) if self.asks else None

    def spread(self):
        # Spread = best ask - best bid
        # Tighter spread = zyada liquid market
        if self.best_bid() and self.best_ask():
            return round(self.best_ask() - self.best_bid(), 2)
        return None

    def display(self):
        # Top 5 levels print karo — visual check ke liye
        print(f"\n{'='*40}")
        print(f"Order Book: {self.symbol}")
        print(f"{'='*40}")
        print(f"{'ASKS':^40}")
        for price, queue in list(self.asks.items())[:5]:
            qty = sum(o.quantity for o in queue)
            print(f"  {price:>10.1f}  |  {qty:.4f}")
        print(f"\n  Spread: {self.spread()}")
        print(f"\n{'BIDS':^40}")
        for price, queue in list(self.bids.items())[:5]:
            qty = sum(o.quantity for o in queue)
            print(f"  {price:>10.1f}  |  {qty:.4f}")
        print(f"{'='*40}\n")
        
    def _match(self, order: Order) -> list[dict]:
        trades = []
        
        # Agar BID aa raha hai toh ASKs se match karo, aur ulta
        book = self.asks if order.side == Side.BID else self.bids
        
        # Jab tak order mein quantity bachi hai aur book empty nahi
        while order.quantity > 0 and book:
            best_price = next(iter(book))  # top of book
            
            # Price check — kya deal ban sakti hai?
            # BID: main max itna dunga, agar ask isse zyada hai toh no deal
            if order.side == Side.BID and best_price > order.price:
                break
            # ASK: main min itne mein dunga, agar bid isse kam hai toh no deal
            if order.side == Side.ASK and best_price < order.price:
                break
            
            # Us price level ki queue ka pehla order lo (FIFO)
            queue = book[best_price]
            passive = queue[0]  # passive = jo pehle se book mein tha
            
            # Kitna fill hoga — dono mein se jo kam hai
            fill_qty = min(order.quantity, passive.quantity)
            
            # Trade record karo
            trades.append({
                "price": best_price,
                "qty": fill_qty,
                "aggressor": order.order_id,   # naya aaya order
                "passive": passive.order_id,    # pehle se tha
            })
            
            # Dono orders se filled quantity hatao
            order.quantity -= fill_qty
            passive.quantity -= fill_qty
            
            # Agar passive order pura fill ho gaya toh queue se hatao
            if passive.quantity == 0:
                queue.popleft()
                del self.orders[passive.order_id]
                # Agar us price pe koi order nahi bacha
                if not queue:
                    del book[best_price]
        
        return trades

    def add_order(self, order: Order) -> list[dict]:
        trades = []
        
        if order.order_type == OrderType.CANCEL:
            # Cancel request
            self._cancel(order.order_id)
            
        elif order.order_type == OrderType.MARKET:
            # Market order — price check nahi, bas fill karo
            order.price = float('inf') if order.side == Side.BID else 0
            trades = self._match(order)
            
        elif order.order_type == OrderType.LIMIT:
            # Pehle match karne ki koshish karo
            trades = self._match(order)
            # Jo quantity fill nahi hui, use book mein daalo
            if order.quantity > 0:
                self._add_to_book(order)
        
        return trades