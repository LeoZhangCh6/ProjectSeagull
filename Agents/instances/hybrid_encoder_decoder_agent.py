"""
Hybrid Encoder-Decoder Agent with Decision Logging

Architecture:
- Encoder: Historical signals → Market state representation
- Decoder: Current state + live price action → Trading decision

This agent uses hard-coded rules for interpretability while maintaining
an encoder-decoder structure that can later be replaced with neural networks.

Features:
- Multi-signal analysis (market context + fundamentals)
- Rule-based decision making
- Comprehensive logging for visualization
- Adaptive position sizing
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from datetime import datetime

import numpy as np
import pandas as pd

from Common.agent_api import build_snapshot_from_signal_ids
from ib_backtester.engine import BaseAgent
from ib_backtester.types import Action, Order, OrderType


@dataclass
class Config:
    """Agent configuration"""
    # Signal window
    window_days: int = 30
    
    # Trading rules
    buy_threshold: float = 0.95    # Buy when price < MA * threshold
    sell_threshold: float = 1.05   # Sell when price > MA * threshold
    fundamental_min: float = 0.0   # Min fundamental score to trade
    
    # Position sizing
    max_position_pct: float = 0.9  # Max 90% of capital
    base_trade_size: int = 10      # Base number of shares
    
    # Risk management
    stop_loss_pct: float = 0.05    # 5% stop loss
    take_profit_pct: float = 0.10  # 10% take profit
    
    # Logging
    log_decisions: bool = True
    log_file: Optional[str] = None


@dataclass
class DecisionLog:
    """Logged decision for visualization"""
    timestamp: str
    bar_index: int
    
    # Encoder outputs (state representation)
    market_trend: float
    market_volatility: float
    fundamental_score: float
    technical_score: float
    
    # Decoder inputs (live signals)
    current_price: float
    price_vs_ma20: float
    price_vs_ma50: float
    volume_ratio: float
    daily_return: float
    
    # State
    position: int
    cash: float
    equity: float
    
    # Decision
    action: str
    quantity: int
    reason: str
    
    # Risk metrics
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]


class HybridEncoderDecoderAgent(BaseAgent):
    """
    Hybrid agent implementing encoder-decoder architecture with hard-coded rules.
    
    The agent follows a clear information flow:
    1. ENCODER: Process historical signals into market state
    2. DECODER: Combine state with live data to make decisions
    3. EXECUTOR: Execute trades with risk management
    4. LOGGER: Record everything for analysis
    """
    
    def __init__(self, cfg: Optional[Config] = None) -> None:
        self.cfg = cfg or Config()
        
        # Agent metadata
        self.symbol = "AAPL"
        self.primary_timespan = "day"
        self.primary_multiplier = 1
        
        # Declare signals used (tracked for usage monitoring)
        self.used_signal_ids = [
            "SPY_day_close",      # Market benchmark (encoder input)
            "AAPL_arq_revenue",   # Fundamental data (encoder input)
        ]
        
        # Internal state
        self._last_snapshot_day: Optional[pd.Timestamp] = None
        self._snapshot_tensor: Optional[np.ndarray] = None
        self._bar_count = 0
        self._entry_price: Optional[float] = None
        
        # Decision logging
        self._decision_log: List[DecisionLog] = []
        
        # Initialize log file if specified
        if self.cfg.log_file:
            self._init_log_file()
    
    def _init_log_file(self):
        """Initialize JSON log file."""
        log_dir = os.path.dirname(self.cfg.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Write initial metadata
        with open(self.cfg.log_file, 'w') as f:
            json.dump({
                'agent': 'HybridEncoderDecoderAgent',
                'symbol': self.symbol,
                'config': asdict(self.cfg),
                'decisions': []
            }, f, indent=2)
    
    def _ensure_snapshot(self, history: pd.DataFrame, now: pd.Timestamp) -> None:
        """
        ENCODER PHASE 1: Fetch and cache historical signal data.
        
        This builds the snapshot tensor that represents what the agent "knows"
        about market history. Updated daily to avoid redundant API calls.
        """
        day = now.normalize()
        if self._last_snapshot_day is not None and self._last_snapshot_day == day:
            return
        
        # Build snapshot from registered signals
        mat, names, index = build_snapshot_from_signal_ids(
            history, 
            now, 
            self.used_signal_ids,
            window_days=self.cfg.window_days
        )
        
        self._snapshot_tensor = mat
        self._last_snapshot_day = day
    
    def _encode_market_state(self) -> Dict[str, float]:
        """
        ENCODER PHASE 2: Transform historical signals into state representation.
        
        This is the "encoding" step - we compress historical data into
        meaningful features that represent current market conditions.
        
        Returns:
            Dictionary of encoded state features
        """
        if self._snapshot_tensor is None or self._snapshot_tensor.size == 0:
            return {
                'market_trend': 0.0,
                'market_volatility': 0.0,
                'fundamental_score': 0.0,
                'technical_score': 0.0
            }
        
        # Extract signal columns (SPY, AAPL fundamentals)
        spy_signal = self._snapshot_tensor[:, 0] if self._snapshot_tensor.shape[1] > 0 else np.array([])
        fundamental_signal = self._snapshot_tensor[:, 1] if self._snapshot_tensor.shape[1] > 1 else np.array([])
        
        # Compute market trend (simple momentum)
        if len(spy_signal) > 10:
            recent_spy = spy_signal[-10:]
            old_spy = spy_signal[-20:-10] if len(spy_signal) > 20 else spy_signal[:10]
            market_trend = float(np.mean(recent_spy) / np.mean(old_spy) - 1) if np.mean(old_spy) > 0 else 0.0
        else:
            market_trend = 0.0
        
        # Compute market volatility
        if len(spy_signal) > 1:
            returns = np.diff(spy_signal) / spy_signal[:-1]
            market_volatility = float(np.std(returns)) if len(returns) > 0 else 0.0
        else:
            market_volatility = 0.0
        
        # Compute fundamental score (growth rate)
        if len(fundamental_signal) > 1:
            # Remove NaNs and compute growth
            clean_fundamental = fundamental_signal[~np.isnan(fundamental_signal)]
            if len(clean_fundamental) > 1:
                fundamental_score = float(clean_fundamental[-1] / clean_fundamental[0] - 1)
            else:
                fundamental_score = 0.0
        else:
            fundamental_score = 0.0
        
        # Technical score (simplified - could expand)
        technical_score = market_trend * (1 - market_volatility)  # Prefer trending + low vol
        
        return {
            'market_trend': market_trend,
            'market_volatility': market_volatility,
            'fundamental_score': fundamental_score,
            'technical_score': technical_score
        }
    
    def _compute_live_signals(self, history: pd.DataFrame, current_price: float) -> Dict[str, float]:
        """
        DECODER PHASE 1: Compute live signals from current price action.
        
        These are real-time indicators computed from recent price/volume data.
        This is the "live" component that gets combined with encoded state.
        
        Returns:
            Dictionary of live signal values
        """
        if history.empty or len(history) < 2:
            return {
                'price_vs_ma20': 1.0,
                'price_vs_ma50': 1.0,
                'volume_ratio': 1.0,
                'daily_return': 0.0
            }
        
        # Moving averages
        close_prices = history["close"].astype(float)
        ma20 = close_prices.tail(20).mean() if len(close_prices) >= 20 else close_prices.mean()
        ma50 = close_prices.tail(50).mean() if len(close_prices) >= 50 else close_prices.mean()
        
        price_vs_ma20 = float(current_price / ma20) if ma20 > 0 else 1.0
        price_vs_ma50 = float(current_price / ma50) if ma50 > 0 else 1.0
        
        # Volume analysis
        volumes = history["volume"].astype(float)
        avg_volume = volumes.tail(20).mean() if len(volumes) >= 20 else volumes.mean()
        current_volume = float(volumes.iloc[-1])
        volume_ratio = float(current_volume / avg_volume) if avg_volume > 0 else 1.0
        
        # Daily return
        if len(close_prices) >= 2:
            prev_close = float(close_prices.iloc[-2])
            daily_return = float((current_price - prev_close) / prev_close) if prev_close > 0 else 0.0
        else:
            daily_return = 0.0
        
        return {
            'price_vs_ma20': price_vs_ma20,
            'price_vs_ma50': price_vs_ma50,
            'volume_ratio': volume_ratio,
            'daily_return': daily_return
        }
    
    def _decode_action(
        self, 
        state: Dict[str, float], 
        live_signals: Dict[str, float],
        position: int
    ) -> tuple[str, int, str]:
        """
        DECODER PHASE 2: Combine encoded state + live signals → trading decision.
        
        This is the core decision logic. Currently uses hard-coded rules,
        but structured to be replaceable with a neural network later.
        
        Args:
            state: Encoded market state (from encoder)
            live_signals: Current price/volume signals
            position: Current position size
        
        Returns:
            (action, quantity, reason) tuple
        """
        # Extract key signals
        price_vs_ma20 = live_signals['price_vs_ma20']
        price_vs_ma50 = live_signals['price_vs_ma50']
        market_trend = state['market_trend']
        fundamental_score = state['fundamental_score']
        technical_score = state['technical_score']
        
        # Rule 1: Check fundamental threshold
        if fundamental_score < self.cfg.fundamental_min:
            return ('HOLD', 0, f'Fundamentals too weak: {fundamental_score:.3f}')
        
        # Rule 2: Buy signal (price below MA + positive market conditions)
        if position == 0:  # Only buy if no position
            buy_conditions = [
                price_vs_ma20 < self.cfg.buy_threshold,
                price_vs_ma50 < self.cfg.buy_threshold,
                market_trend > -0.05,  # Market not crashing
                technical_score > 0    # Positive technical
            ]
            
            if sum(buy_conditions) >= 3:  # Need 3 out of 4 conditions
                quantity = self.cfg.base_trade_size
                reasons = []
                if buy_conditions[0]: reasons.append('below MA20')
                if buy_conditions[1]: reasons.append('below MA50')
                if buy_conditions[2]: reasons.append('market stable')
                if buy_conditions[3]: reasons.append('tech positive')
                
                return ('BUY', quantity, f'Buy signal: {", ".join(reasons)}')
        
        # Rule 3: Sell signal (price above MA or risk management)
        if position > 0:
            sell_conditions = [
                price_vs_ma20 > self.cfg.sell_threshold,
                price_vs_ma50 > self.cfg.sell_threshold,
                market_trend < -0.10,  # Market dropping
            ]
            
            if any(sell_conditions):
                quantity = abs(position)
                reasons = []
                if sell_conditions[0]: reasons.append('above MA20 threshold')
                if sell_conditions[1]: reasons.append('above MA50 threshold')
                if sell_conditions[2]: reasons.append('market downturn')
                
                return ('SELL', quantity, f'Sell signal: {", ".join(reasons)}')
        
        return ('HOLD', 0, 'No clear signal')
    
    def _check_risk_management(
        self, 
        current_price: float, 
        position: int
    ) -> tuple[Optional[str], Optional[int], Optional[str]]:
        """
        Check stop-loss and take-profit levels.
        
        Returns:
            (action, quantity, reason) if risk trigger hit, else (None, None, None)
        """
        if position == 0 or self._entry_price is None:
            return (None, None, None)
        
        pnl_pct = (current_price - self._entry_price) / self._entry_price
        
        # Stop loss
        if pnl_pct < -self.cfg.stop_loss_pct:
            return ('SELL', abs(position), f'Stop loss triggered: {pnl_pct:.2%}')
        
        # Take profit
        if pnl_pct > self.cfg.take_profit_pct:
            return ('SELL', abs(position), f'Take profit triggered: {pnl_pct:.2%}')
        
        return (None, None, None)
    
    def _execute_trade(
        self, 
        ib, 
        contract, 
        action: str, 
        quantity: int, 
        current_price: float
    ):
        """Execute the trade and update internal state."""
        if quantity == 0:
            return
        
        oid = ib.nextOrderId()
        
        if action == 'BUY':
            ib.placeOrder(oid, contract, Order(
                action=Action.BUY, 
                totalQuantity=int(quantity), 
                orderType=OrderType.MKT
            ))
            self._entry_price = current_price
        
        elif action == 'SELL':
            ib.placeOrder(oid, contract, Order(
                action=Action.SELL, 
                totalQuantity=int(quantity), 
                orderType=OrderType.MKT
            ))
            if quantity == abs(ib.get_portfolio_state()['position']):
                self._entry_price = None  # Closed position
    
    def _log_decision(
        self,
        timestamp: pd.Timestamp,
        state: Dict[str, float],
        live_signals: Dict[str, float],
        current_price: float,
        portfolio_state: Dict,
        action: str,
        quantity: int,
        reason: str
    ):
        """Log decision for later visualization."""
        if not self.cfg.log_decisions:
            return
        
        log_entry = DecisionLog(
            timestamp=timestamp.isoformat(),
            bar_index=self._bar_count,
            
            # Encoded state
            market_trend=state['market_trend'],
            market_volatility=state['market_volatility'],
            fundamental_score=state['fundamental_score'],
            technical_score=state['technical_score'],
            
            # Live signals
            current_price=current_price,
            price_vs_ma20=live_signals['price_vs_ma20'],
            price_vs_ma50=live_signals['price_vs_ma50'],
            volume_ratio=live_signals['volume_ratio'],
            daily_return=live_signals['daily_return'],
            
            # Portfolio state
            position=portfolio_state['position'],
            cash=portfolio_state['cash'],
            equity=portfolio_state['equity'],
            
            # Decision
            action=action,
            quantity=quantity,
            reason=reason,
            
            # Risk levels
            entry_price=self._entry_price,
            stop_loss=self._entry_price * (1 - self.cfg.stop_loss_pct) if self._entry_price else None,
            take_profit=self._entry_price * (1 + self.cfg.take_profit_pct) if self._entry_price else None
        )
        
        self._decision_log.append(log_entry)
        
        # Append to log file if configured
        if self.cfg.log_file:
            self._append_to_log_file(log_entry)
    
    def _append_to_log_file(self, log_entry: DecisionLog):
        """Append decision to JSON log file."""
        try:
            with open(self.cfg.log_file, 'r') as f:
                data = json.load(f)
            
            data['decisions'].append(asdict(log_entry))
            
            with open(self.cfg.log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    # =========================================================================
    # BaseAgent Interface Implementation
    # =========================================================================
    
    def on_start(self, ib, contract) -> None:
        """Called once at the start of the backtest."""
        print(f"HybridEncoderDecoderAgent starting for {self.symbol}")
        print(f"Using signals: {self.used_signal_ids}")
        print(f"Config: buy_threshold={self.cfg.buy_threshold}, sell_threshold={self.cfg.sell_threshold}")
    
    def on_bar(self, ib, contract, history: pd.DataFrame) -> None:
        """
        Called on each new bar. Main agent loop.
        
        Flow:
        1. ENCODER: Build snapshot → Encode market state
        2. DECODER: Compute live signals → Decide action
        3. EXECUTOR: Execute trade
        4. LOGGER: Record decision
        """
        if history.empty:
            return
        
        self._bar_count += 1
        now = pd.to_datetime(history["time"].iloc[-1])
        current_price = float(history["close"].iloc[-1])
        state = ib.get_portfolio_state()
        
        # ENCODER: Update snapshot and encode market state
        self._ensure_snapshot(history, now)
        encoded_state = self._encode_market_state()
        
        # DECODER: Compute live signals
        live_signals = self._compute_live_signals(history, current_price)
        
        # Check risk management first (overrides strategy)
        risk_action, risk_qty, risk_reason = self._check_risk_management(
            current_price, state['position']
        )
        
        if risk_action:
            action, quantity, reason = risk_action, risk_qty, risk_reason
        else:
            # Decode action from state + live signals
            action, quantity, reason = self._decode_action(
                encoded_state, live_signals, state['position']
            )
        
        # Apply position sizing constraints
        if action == 'BUY':
            max_shares = int(state['cash'] * self.cfg.max_position_pct / current_price)
            quantity = min(quantity, max_shares)
        elif action == 'SELL':
            quantity = min(quantity, abs(state['position']))
        
        # EXECUTOR: Execute trade
        if quantity > 0:
            self._execute_trade(ib, contract, action, quantity, current_price)
        
        # LOGGER: Record decision
        self._log_decision(
            now, encoded_state, live_signals, current_price, 
            state, action, quantity, reason
        )
    
    def on_end(self, ib, contract) -> None:
        """Called once at the end of the backtest."""
        print(f"\nHybridEncoderDecoderAgent finished")
        print(f"Total decisions logged: {len(self._decision_log)}")
        
        if self.cfg.log_file:
            print(f"Decision log saved to: {self.cfg.log_file}")
            print(f"Visualize with: python Scripts/visualize_agent.py {self.cfg.log_file}")


def create_agent() -> BaseAgent:
    """Factory function to create agent instance."""
    # Configure agent
    config = Config(
        window_days=30,
        buy_threshold=0.97,
        sell_threshold=1.03,
        fundamental_min=-0.5,  # Allow some negative growth
        base_trade_size=10,
        stop_loss_pct=0.05,
        take_profit_pct=0.10,
        log_decisions=True,
        log_file='logs/hybrid_agent_decisions.json'
    )
    
    return HybridEncoderDecoderAgent(config)
