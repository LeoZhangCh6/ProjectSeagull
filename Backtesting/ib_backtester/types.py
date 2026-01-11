from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SecurityType(str, Enum):
    STK = "STK"
    OPT = "OPT"
    FUT = "FUT"
    CASH = "CASH"


class OrderType(str, Enum):
    MKT = "MKT"
    LMT = "LMT"


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Contract:
    symbol: str
    secType: SecurityType = SecurityType.STK
    exchange: str = "SMART"
    currency: str = "USD"


@dataclass
class Order:
    action: Action
    totalQuantity: int
    orderType: OrderType = OrderType.MKT
    lmtPrice: Optional[float] = None
    tif: str = "DAY"
    orderId: Optional[int] = field(default=None, compare=False)


