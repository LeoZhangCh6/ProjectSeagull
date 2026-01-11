import pandas as pd

from ..engine import BaseAgent
from ..types import Action, Contract, Order, OrderType


class SmaCrossAgent(BaseAgent):
    def __init__(self, fast: int = 10, slow: int = 20, trade_size: int = 10) -> None:
        self.fast = int(fast)
        self.slow = int(slow)
        self.trade_size = int(trade_size)
        self.in_position: bool = False

    def on_start(self, ib, contract: Contract) -> None:
        pass

    def on_bar(self, ib, contract: Contract, history: pd.DataFrame) -> None:
        closes = history["close"].astype(float)
        if len(closes) < max(self.fast, self.slow) + 1:
            return
        fast_sma = closes.rolling(self.fast).mean()
        slow_sma = closes.rolling(self.slow).mean()

        prev_fast = fast_sma.iloc[-2]
        prev_slow = slow_sma.iloc[-2]
        curr_fast = fast_sma.iloc[-1]
        curr_slow = slow_sma.iloc[-1]

        crossed_up = prev_fast <= prev_slow and curr_fast > curr_slow
        crossed_down = prev_fast >= prev_slow and curr_fast < curr_slow

        if crossed_up and not self.in_position:
            oid = ib.nextOrderId()
            order = Order(action=Action.BUY, totalQuantity=self.trade_size, orderType=OrderType.MKT)
            ib.placeOrder(oid, contract, order)
            self.in_position = True
            
        elif crossed_down and self.in_position:
            oid = ib.nextOrderId()
            order = Order(action=Action.SELL, totalQuantity=self.trade_size, orderType=OrderType.MKT)
            ib.placeOrder(oid, contract, order)
            self.in_position = False

    def on_end(self, ib, contract: Contract) -> None:
        pass


