# Position Validation Rules

## Overview

The backtesting engine enforces strict position management to prevent short selling and ensure realistic trading constraints.

## Rules

### 1. No Short Selling
Agents **cannot sell shares they don't hold**.

**Rejection Scenarios:**
- Position = 0: All SELL orders rejected
- Position < 0: All SELL orders rejected
- Sell Quantity > Position: Order rejected

### 2. Position Validation
All SELL orders are validated before execution:
```python
if order.action == Action.SELL:
    if broker.position <= 0:
        # REJECTED: No shares to sell
    elif order.totalQuantity > broker.position:
        # REJECTED: Insufficient shares
```

### 3. Order Rejection
Invalid orders are:
- **Logged** with warning messages
- **Not executed** (removed from order queue)
- **Not filled** (no impact on portfolio)

## Agent Implementation

### Check Position Before Selling

```python
def on_bar(self, ib, contract, data):
    state = ib.get_portfolio_state()
    current_position = state['position']
    
    # Only sell if you have shares
    if current_position > 0:
        sell_quantity = min(10, current_position)  # Don't exceed position
        ib.placeOrder(ib.nextOrderId(), contract, 
                     Order(action=Action.SELL, totalQuantity=sell_quantity))
```

### Best Practices

1. **Always check position** before placing sell orders
2. **Cap sell quantity** to current position: `min(desired_qty, position)`
3. **Handle rejections gracefully** (watch for warning logs)
4. **Track position** in agent state if needed

## Testing

Run the position validation test:

```bash
python Scripts/test_position_validation.py
```

This test demonstrates:
- ✅ Selling with 0 position is rejected
- ✅ Selling more than held is rejected  
- ✅ Valid sell orders are accepted
- ✅ Position tracking works correctly

## Warning Messages

When orders are rejected, you'll see console warnings:

```
[WARNING] Order 123 REJECTED: Cannot SELL 10 shares - current position is 0
[WARNING] Order 456 REJECTED: Cannot SELL 100 shares - only 50 shares available
```

## Benefits

1. **Realistic trading** - Matches real broker constraints
2. **Prevents errors** - Catches agent logic bugs
3. **Clear feedback** - Warning messages help debugging
4. **Portfolio integrity** - Ensures valid position tracking

## Impact on Existing Agents

Existing agents that attempt short selling will now:
- See warning messages in console
- Have those orders rejected
- Need to be updated to check positions

Review and update agents if you see rejection warnings during backtests.
