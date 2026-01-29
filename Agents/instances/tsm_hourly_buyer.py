"""
Minimal TSM Agent - Buys 1 share of TSM every hour.

This is a minimal example agent that demonstrates the basic structure.
It doesn't read any external signals - just buys 1 share of TSM on every bar.
"""

import pandas as pd
from typing import Optional

from ib_backtester.engine import BaseAgent
from ib_backtester.types import Action, Order, OrderType


class TSMHourlyBuyerAgent(BaseAgent):
    """
    A minimal agent that buys 1 share of TSM every hour.
    No signals, no complex logic - just a simple buy-every-bar strategy.
    """
    
    def __init__(self) -> None:
        # Trading symbol - Taiwan Semiconductor (TSM)
        self.symbol = "TSM"
        
        # Use hourly bars
        self.primary_timespan = "hour"
        self.primary_multiplier = 1
        
        # No external signals needed
        self.used_signal_ids = []
        
        # Track how many shares we've bought
        self._total_bought = 0

    def on_start(self, ib, contract) -> None:
        """Called once at the start of the simulation."""
        print(f"TSM Hourly Buyer Agent started. Trading {self.symbol}.")

    def on_bar(self, ib, contract, history: pd.DataFrame) -> None:
        """Called on each new bar (every hour)."""
        if history.empty:
            return
        
        # Get current price and portfolio state
        price = float(history["close"].iloc[-1])
        state = ib.get_portfolio_state()
        cash = state["cash"]
        
        # Only buy if we have enough cash for 1 share
        if cash < price:
            return
        
        # Buy 1 share of TSM
        qty = 1
        oid = ib.nextOrderId()
        ib.placeOrder(
            oid, 
            contract, 
            Order(action=Action.BUY, totalQuantity=qty, orderType=OrderType.MKT)
        )
        
        self._total_bought += qty

    def on_end(self, ib, contract) -> None:
        """Called once at the end of the simulation."""
        state = ib.get_portfolio_state()
        print(f"TSM Hourly Buyer Agent finished.")
        print(f"  Total shares bought: {self._total_bought}")
        print(f"  Final position: {state['position']} shares")
        print(f"  Final cash: ${state['cash']:.2f}")
        print(f"  Final equity: ${state['equity']:.2f}")


def create_agent() -> BaseAgent:
    """Factory function required by the agent loading system."""
    return TSMHourlyBuyerAgent()
