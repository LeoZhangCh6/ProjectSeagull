from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
from datetime import timedelta

from Common.massive_client import get_aggregate_bars
from .types import Action, Contract, Order, OrderType


@dataclass
class FillReport:
    orderId: int
    action: Action
    quantity: int
    price: float
    commission: float
    timestamp: int


@dataclass
class AgentState:
    """Snapshot of agent's internal state at a given bar, for visualization."""
    timestamp: int
    time: str
    custom: Dict[str, Any] = field(default_factory=dict)  # Agent-defined state variables


class BacktestBroker:
    def __init__(self, initial_cash: float = 100000.0, commission_rate: float = 0.0005) -> None:
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.position: int = 0
        self.avg_cost: float = 0.0
        self.commission_rate = float(commission_rate)
        self.trades: List[FillReport] = []

    def _apply_fill(self, action: Action, quantity: int, price: float, timestamp: int, orderId: int) -> FillReport:
        notional = price * quantity
        commission = abs(notional) * self.commission_rate
        if action == Action.BUY:
            # Update average cost for long position
            new_position = self.position + quantity
            if self.position >= 0:
                total_cost = self.avg_cost * max(self.position, 0) + notional + commission
                self.avg_cost = total_cost / max(new_position, 1e-9)
            else:
                # Reducing or flipping a short (not fully modeled, but handle cash and position)
                pass
            self.position = new_position
            self.cash -= notional + commission
        else:
            # SELL
            self.position -= quantity
            self.cash += notional - commission
            if self.position == 0:
                self.avg_cost = 0.0

        report = FillReport(orderId=orderId, action=action, quantity=quantity, price=price, commission=commission, timestamp=timestamp)
        self.trades.append(report)
        return report

    def market_fill(self, action: Action, quantity: int, bar_open: float, bar_timestamp: int, orderId: int) -> FillReport:
        return self._apply_fill(action, quantity, bar_open, bar_timestamp, orderId)

    def limit_fill(self, action: Action, quantity: int, limit_price: float, bar_low: float, bar_high: float, bar_timestamp: int, orderId: int) -> Optional[FillReport]:
        if action == Action.BUY and bar_low <= limit_price:
            return self._apply_fill(action, quantity, limit_price, bar_timestamp, orderId)
        if action == Action.SELL and bar_high >= limit_price:
            return self._apply_fill(action, quantity, limit_price, bar_timestamp, orderId)
        return None


class IBFacade:
    def __init__(self, env: "IBBacktestEnv") -> None:
        self._env = env
        self._next_order_id: int = 1

    def nextOrderId(self) -> int:
        oid = self._next_order_id
        self._next_order_id += 1
        return oid

    def get_portfolio_state(self) -> Dict[str, float]:
        broker = self._env.broker
        # Use last known close as mark price
        if 0 <= self._env.current_index < len(self._env.data):
            price = float(self._env.data.iloc[self._env.current_index]["close"])
        else:
            price = 0.0
        equity = float(broker.cash + broker.position * price)
        return {
            "cash": float(broker.cash),
            "position": int(broker.position),
            "avg_cost": float(broker.avg_cost),
            "mark_price": price,
            "equity": equity,
        }

    def reqHistoricalData(
        self,
        contract: Contract,
        endDateTime: Optional[str] = None,
        durationStr: Optional[str] = None,
        barSizeSetting: Optional[str] = None,
        whatToShow: Optional[str] = None,
        useRTH: bool = True,
        formatDate: int = 1,
    ) -> pd.DataFrame:
        # For backtesting, simply return the loaded dataset for the contract
        return self._env.get_data(contract)

    def placeOrder(self, orderId: int, contract: Contract, order: Order) -> None:
        """
        Place an order.
        
        Args:
            orderId: Unique order identifier
            contract: Contract to trade
            order: Order details (action, quantity, type, etc.)
            
        Note:
            SELL orders will be rejected if:
            - Current position is <= 0 (no shares held)
            - Order quantity exceeds current position (insufficient shares)
        """
        self._env._submit_order(orderId, contract, order)


class IBBacktestEnv:
    def __init__(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timespan: str = "minute",
        multiplier: int = 1,
        initial_cash: float = 100000.0,
        commission_rate: float = 0.0005,
        data: Optional[pd.DataFrame] = None,
    ) -> None:
        if data is None:
            if not (symbol and start_date and end_date):
                raise ValueError("Provide either a DataFrame via 'data' or (symbol, start_date, end_date).")
            df = get_aggregate_bars(symbol, start_date, end_date, timespan=timespan, multiplier=multiplier)
            if df is None or df.empty:
                raise RuntimeError("No data returned for the given parameters.")
            self.data = df.reset_index(drop=True)
        else:
            self.data = data.reset_index(drop=True)

        # State
        self.broker = BacktestBroker(initial_cash=initial_cash, commission_rate=commission_rate)
        self.current_index: int = 0
        self.pending_orders: List[Dict] = []
        self.ib = IBFacade(self)

        # Contract inferred from data if possible
        first_symbol = self.data["symbol"].iloc[0]
        self.contract = Contract(symbol=str(first_symbol))

        # Performance tracking
        self.portfolio_history: List[Dict] = []
        
        # Agent state history for visualization
        self.agent_states: List[AgentState] = []

        # Trading window timestamps (for plotting)
        self.trading_start_timestamp: Optional[int] = None
        self.trading_end_timestamp: Optional[int] = None

    def get_data(self, contract: Contract) -> pd.DataFrame:
        assert contract.symbol == self.contract.symbol, "Single-symbol backtester only"
        return self.data.copy()
    
    def record_agent_state(self, custom: Dict[str, Any]) -> None:
        """
        Record agent's internal state at current bar for visualization.
        Agents should call this in on_bar() to log their decision state.
        
        Args:
            custom: Dictionary of agent-defined state variables (e.g., signals, predictions)
        """
        if 0 <= self.current_index < len(self.data):
            row = self.data.iloc[self.current_index]
            self.agent_states.append(AgentState(
                timestamp=int(row["timestamp"]),
                time=str(row["time"]),
                custom=custom.copy(),
            ))

    def _submit_order(self, orderId: int, contract: Contract, order: Order) -> None:
        assert contract.symbol == self.contract.symbol, "Single-symbol backtester only"
        # Orders execute on next bar
        exec_index = min(self.current_index + 1, len(self.data) - 1)
        self.pending_orders.append(
            {"orderId": orderId, "contract": contract, "order": order, "exec_index": exec_index}
        )

    def buy(self, quantity: int) -> int:
        """
        Place a market buy order.
        
        Args:
            quantity: Number of shares to buy
            
        Returns:
            Order ID
        """
        oid = self.ib.nextOrderId()
        self._submit_order(oid, self.contract, Order(action=Action.BUY, totalQuantity=quantity, orderType=OrderType.MKT))
        return oid

    def sell(self, quantity: int) -> int:
        """
        Place a market sell order.
        
        Args:
            quantity: Number of shares to sell
            
        Returns:
            Order ID
            
        Note:
            Orders will be rejected if:
            - Current position is <= 0 (no shares held)
            - Quantity exceeds current position (insufficient shares)
            Agents should check their position before selling.
        """
        oid = self.ib.nextOrderId()
        self._submit_order(oid, self.contract, Order(action=Action.SELL, totalQuantity=quantity, orderType=OrderType.MKT))
        return oid

    def _mark_to_market(self, idx: int) -> None:
        row = self.data.iloc[idx]
        price = float(row["close"])
        equity = self.broker.cash + self.broker.position * price
        self.portfolio_history.append(
            {
                "timestamp": int(row["timestamp"]),
                "time": row["time"],
                "close": price,
                "cash": self.broker.cash,
                "position": self.broker.position,
                "equity": equity,
            }
        )

    def _process_orders_for_bar(self, idx: int) -> None:
        bar = self.data.iloc[idx]
        bar_open = float(bar["open"])
        bar_low = float(bar["low"])
        bar_high = float(bar["high"])
        ts = int(bar["timestamp"])

        remaining: List[Dict] = []
        for item in self.pending_orders:
            if item["exec_index"] != idx:
                remaining.append(item)
                continue
            order: Order = item["order"]
            
            # Validate: cannot sell shares you don't hold
            if order.action == Action.SELL:
                if self.broker.position <= 0:
                    # Reject sell order if no position
                    print(f"[WARNING] Order {item['orderId']} REJECTED: Cannot SELL {order.totalQuantity} shares - current position is {self.broker.position}")
                    continue
                elif order.totalQuantity > self.broker.position:
                    # Reject sell order if quantity exceeds position
                    print(f"[WARNING] Order {item['orderId']} REJECTED: Cannot SELL {order.totalQuantity} shares - only {self.broker.position} shares available")
                    continue
            
            if order.orderType == OrderType.MKT:
                self.broker.market_fill(order.action, int(order.totalQuantity), bar_open, ts, item["orderId"])
            elif order.orderType == OrderType.LMT and order.lmtPrice is not None:
                fill = self.broker.limit_fill(order.action, int(order.totalQuantity), float(order.lmtPrice), bar_low, bar_high, ts, item["orderId"])
                if fill is None:
                    # Keep the order to attempt on next bar
                    item["exec_index"] = min(idx + 1, len(self.data) - 1)
                    remaining.append(item)
            else:
                # Unsupported types are ignored in this minimal engine
                pass
        self.pending_orders = remaining

    def run(self, agent: "BaseAgent", trading_days: int = 14) -> pd.DataFrame:
        """
        Run backtest simulation.
        
        At the beginning of each day, agents receive a daily snapshot of available signals.
        They can trade throughout the day until trading_days have elapsed.
        
        Args:
            agent: The trading agent to run
            trading_days: Number of trading days to simulate
            
        Returns:
            DataFrame with portfolio history (equity curve)
        """
        agent.on_start(self.ib, self.contract)
        
        # Trading starts from the first bar
        first_time = pd.to_datetime(self.data["time"].iloc[0])
        self.trading_start_timestamp = int(self.data["timestamp"].iloc[0])
        
        # Determine trading end based on trading_days
        times = pd.to_datetime(self.data["time"])
        trading_end_time = first_time + timedelta(days=int(trading_days))
        end_idx_list = times.index[times >= trading_end_time].tolist()
        trading_end_index = end_idx_list[0] if len(end_idx_list) > 0 else len(self.data) - 1
        self.trading_end_timestamp = int(self.data["timestamp"].iloc[trading_end_index])
        
        # Track current day for daily signal snapshots
        current_day: Optional[str] = None

        for i in range(len(self.data)):
            self.current_index = i
            row = self.data.iloc[i]
            bar_day = pd.to_datetime(row["time"]).strftime("%Y-%m-%d")
            
            # Notify agent of new day (for daily signal snapshot)
            if bar_day != current_day:
                current_day = bar_day
                if hasattr(agent, "on_day_start"):
                    agent.on_day_start(self.ib, self.contract, current_day)
            
            # Agent observes current bar snapshot
            agent.on_bar(self.ib, self.contract, self.data.iloc[: i + 1].copy())
            
            # Then orders execute on next bar open
            self._process_orders_for_bar(i)
            self._mark_to_market(i)
            
            if i >= trading_end_index:
                break
                
        agent.on_end(self.ib, self.contract)
        return pd.DataFrame(self.portfolio_history)


class BaseAgent:
    """
    Base class for trading agents.
    
    Agents receive daily signal snapshots at the start of each day via on_day_start(),
    then trade throughout the day via on_bar() calls.
    
    To enable state visualization in plots, call env.record_agent_state() in on_bar()
    with a dict of your agent's internal state (signals, predictions, etc).
    """
    
    def on_start(self, ib: IBFacade, contract: Contract) -> None:
        """Called once at the beginning of the backtest."""
        pass
    
    def on_day_start(self, ib: IBFacade, contract: Contract, date: str) -> None:
        """
        Called at the start of each trading day.
        
        Use this to fetch/refresh daily signal snapshots before intraday trading.
        
        Args:
            ib: IB facade for placing orders and getting portfolio state
            contract: The trading contract
            date: The current date in YYYY-MM-DD format
        """
        pass

    def on_bar(self, ib: IBFacade, contract: Contract, history: pd.DataFrame) -> None:
        """
        Called for each bar during the simulation.
        
        Args:
            ib: IB facade for placing orders and getting portfolio state
            contract: The trading contract  
            history: OHLCV data up to and including the current bar
        """
        pass

    def on_end(self, ib: IBFacade, contract: Contract) -> None:
        """Called once at the end of the backtest."""
        pass


