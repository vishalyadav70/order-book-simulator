# Price-time priority matching

from dataclasses import dataclass, field
from enum import Enum
import time

# Side-order BID (kharid) hai ya ASK (becha)
class Side(Enum):
    BID = "bid"     #buyer
    ASK = "ask"     #seller

# OrderType- teen tarah ke order hote hai exchange pe
class OrderType(Enum):
    LIMIT = "limit"    # specific price pe hi execute karo
    MARKET = "market"  # abhi best available price pe execute karo
    CANCEL = "cancel"  # pehle se placed order cancel karo

# Order — ek single trade request ka blueprint
# @dataclass automatically __init__, __repr__ banata hai

@dataclass
class Order:
    order_id: int   # har order ka unique ID
    side: Side      # BID ya ASK
    price: float    # kitne price pe kharidna/bechna hai
    quantity: float # kitna kharidna/bechna hai (BTC mein)

    # default = LIMIT, agar specify na karo toh
    order_type: OrderType = OrderType.LIMIT
    
    # time.time_ns() = nanosecond timestamp
    # field(default_factory=...) isliye use kiya kyunki
    # har Order apna alag timestamp chahta hai
    
    timestamp: float = field(default_factory=time.time_ns)
    
    symbol: str = "BTC-USDT"