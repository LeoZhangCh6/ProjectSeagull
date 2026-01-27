"""
Test script to verify position validation (no short selling rule).

This script demonstrates that:
1. Agents cannot sell shares when position is 0
2. Agents cannot sell more shares than they hold
3. Valid sell orders (within position) are accepted
"""

import os
import sys

# Add project root to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pandas as pd
from Backtesting.ib_backtester.engine import IBBacktestEnv, BaseAgent
from Backtesting.ib_backtester.types import Contract, Action


class PositionTestAgent(BaseAgent):
    """Test agent that attempts various sell scenarios."""
    
    def __init__(self):
        self.symbol = "TEST"
        self.used_signal_ids = []
        self.test_phase = 0
    
    def on_start(self, ib, contract):
        """Initialize."""
        print("\n=== Position Validation Test Agent Started ===")
        print(f"Initial state: {ib.get_portfolio_state()}")
    
    def on_bar(self, ib, contract, data):
        """Test different sell scenarios."""
        state = ib.get_portfolio_state()
        
        if self.test_phase == 0:
            # Phase 0: Try to sell when position is 0 (should be REJECTED)
            print(f"\n[Phase 0] Current position: {state['position']}")
            print("[Phase 0] Attempting to SELL 10 shares with 0 position...")
            ib.placeOrder(ib.nextOrderId(), contract, 
                         Order(action=Action.SELL, totalQuantity=10))
            self.test_phase = 1
            
        elif self.test_phase == 1:
            # Phase 1: Buy some shares
            print(f"\n[Phase 1] Current position: {state['position']}")
            print("[Phase 1] Buying 50 shares...")
            env = ib._env
            env.buy(50)
            self.test_phase = 2
            
        elif self.test_phase == 2:
            # Phase 2: Try to sell more than we have (should be REJECTED)
            print(f"\n[Phase 2] Current position: {state['position']}")
            print("[Phase 2] Attempting to SELL 100 shares (only have 50)...")
            env = ib._env
            env.sell(100)
            self.test_phase = 3
            
        elif self.test_phase == 3:
            # Phase 3: Sell valid amount (should SUCCEED)
            print(f"\n[Phase 3] Current position: {state['position']}")
            print("[Phase 3] Selling 25 shares (valid)...")
            env = ib._env
            env.sell(25)
            self.test_phase = 4
            
        elif self.test_phase == 4:
            # Phase 4: Final state
            print(f"\n[Phase 4] Final position: {state['position']}")
            print(f"[Phase 4] Final equity: ${state['equity']:.2f}")
    
    def on_end(self, ib, contract):
        """Cleanup."""
        final_state = ib.get_portfolio_state()
        print("\n=== Test Complete ===")
        print(f"Final position: {final_state['position']} shares")
        print(f"Final cash: ${final_state['cash']:.2f}")
        print(f"Final equity: ${final_state['equity']:.2f}")
        print("\nExpected results:")
        print("  - Phase 0 SELL order: REJECTED (no position)")
        print("  - Phase 2 SELL order: REJECTED (insufficient shares)")
        print("  - Phase 3 SELL order: ACCEPTED (valid)")
        print("  - Final position: 25 shares (bought 50, sold 25)")


def create_agent():
    """Factory function."""
    return PositionTestAgent()


def main():
    """Run the test."""
    # Create synthetic test data
    print("Creating test environment...")
    
    # Generate 10 bars of synthetic data
    data = pd.DataFrame({
        'timestamp': [1000000 + i * 1000 for i in range(10)],
        'time': [f"2024-01-01 09:{30+i}:00" for i in range(10)],
        'symbol': ['TEST'] * 10,
        'open': [100.0] * 10,
        'high': [101.0] * 10,
        'low': [99.0] * 10,
        'close': [100.0] * 10,
        'volume': [1000] * 10,
    })
    
    # Create backtest environment
    env = IBBacktestEnv(
        data=data,
        initial_cash=100000.0,
        commission_rate=0.001
    )
    
    # Run test agent
    agent = PositionTestAgent()
    results = env.run(agent, trading_days=365)
    
    print("\n=== Trade History ===")
    for i, trade in enumerate(env.broker.trades, 1):
        print(f"{i}. {trade.action.value} {trade.quantity} @ ${trade.price:.2f} "
              f"(commission: ${trade.commission:.2f})")
    
    print("\nTest complete! Check warnings above for rejected orders.")


if __name__ == "__main__":
    # Import Order here to avoid circular import
    from Backtesting.ib_backtester.types import Order
    main()
