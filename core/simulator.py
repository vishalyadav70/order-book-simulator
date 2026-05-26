import asyncio
import time
import numpy as np
from core.order import Order, Side, OrderType
from core.order_book import OrderBook

class EventDrivenSimulator:
    def __init__(self, symbol: str = "BTC-USDT"):
        self.book = OrderBook(symbol)
        self.queue = asyncio.Queue()
        self.latencies = []
        self.total_trades = 0
        self.total_orders = 0

    async def process_events(self):
        while True:
            order = await self.queue.get()
            t0 = time.time_ns()
            trades = self.book.add_order(order)
            latency_ns = time.time_ns() - t0
            self.latencies.append(latency_ns)
            self.total_trades += len(trades)
            self.total_orders += 1
            self.queue.task_done()

    async def feed_orders(self, orders: list):
        for order in orders:
            await self.queue.put(order)
        await self.queue.join()

    async def run(self, orders: list):
        consumer = asyncio.create_task(self.process_events())
        await self.feed_orders(orders)
        consumer.cancel()

    def stats(self):
        if not self.latencies:
            return
        arr = np.array(self.latencies)
        print(f"\n{'='*40}")
        print(f"Simulation Stats")
        print(f"{'='*40}")
        print(f"Total orders   : {self.total_orders:,}")
        print(f"Total trades   : {self.total_trades:,}")
        print(f"Avg latency    : {np.mean(arr):.0f} ns")
        print(f"P50 latency    : {np.percentile(arr, 50):.0f} ns")
        print(f"P99 latency    : {np.percentile(arr, 99):.0f} ns")
        print(f"P99.9 latency  : {np.percentile(arr, 99.9):.0f} ns")
        print(f"{'='*40}\n")


class FastSimulator:
    """
    Queue-free direct processing — maximum speed ke liye
    asyncio overhead hataya, direct loop use kiya
    """
    def __init__(self, symbol: str = "BTC-USDT"):
        self.book = OrderBook(symbol)
        self.latencies = []
        self.total_trades = 0
        self.total_orders = 0

    def run(self, orders: list):
        # asyncio queue hataya — direct process karo
        # har order seedha matching engine ko
        latencies = self.latencies
        append = latencies.append  # local reference — faster lookup

        for order in orders:
            t0 = time.time_ns()
            trades = self.book.add_order(order)
            append(time.time_ns() - t0)
            self.total_trades += len(trades)

        self.total_orders = len(orders)

    def stats(self):
        if not self.latencies:
            return
        arr = np.array(self.latencies)
        print(f"\n{'='*45}")
        print(f"FastSimulator Stats")
        print(f"{'='*45}")
        print(f"Total orders   : {self.total_orders:,}")
        print(f"Total trades   : {self.total_trades:,}")
        print(f"Avg latency    : {np.mean(arr):.0f} ns")
        print(f"P50 latency    : {np.percentile(arr, 50):.0f} ns")
        print(f"P95 latency    : {np.percentile(arr, 95):.0f} ns")
        print(f"P99 latency    : {np.percentile(arr, 99):.0f} ns")
        print(f"P99.9 latency  : {np.percentile(arr, 99.9):.0f} ns")
        print(f"{'='*45}\n")