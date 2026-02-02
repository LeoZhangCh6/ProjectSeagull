"""Design templates for Visual Agent Designer.

Pre-built templates for common trading strategies.
"""

from typing import Dict, List, Optional


# Template definitions
TEMPLATES = {
    "sma_crossover": {
        "name": "SMA Crossover (Improved)",
        "description": "Buy when 20-day SMA crosses above 50-day SMA, sell on cross below. Uses crossover detection for clear signals.",
        "symbol": "AAPL",
        "primary_timespan": "day",
        "primary_multiplier": 1,
        "graph": {
            "nodes": [
                {
                    "id": "signal-1",
                    "type": "signal",
                    "position": {"x": 50, "y": 150},
                    "data": {
                        "label": "Price",
                        "signalId": "AAPL_day_close",
                        "description": "Daily close price"
                    }
                },
                {
                    "id": "slice-1",
                    "type": "slice",
                    "position": {"x": 260, "y": 50},
                    "data": {
                        "label": "Last 50",
                        "n": 50
                    }
                },
                {
                    "id": "slice-2",
                    "type": "slice",
                    "position": {"x": 260, "y": 250},
                    "data": {
                        "label": "Last 20",
                        "n": 20
                    }
                },
                {
                    "id": "mean-1",
                    "type": "mean",
                    "position": {"x": 470, "y": 50},
                    "data": {
                        "label": "Slow SMA (50)"
                    }
                },
                {
                    "id": "mean-2",
                    "type": "mean",
                    "position": {"x": 470, "y": 250},
                    "data": {
                        "label": "Fast SMA (20)"
                    }
                },
                {
                    "id": "crossover-1",
                    "type": "crossover",
                    "position": {"x": 680, "y": 150},
                    "data": {
                        "label": "SMA Crossover"
                    }
                },
                {
                    "id": "subtract-1",
                    "type": "subtract",
                    "position": {"x": 920, "y": 150},
                    "data": {
                        "label": "Buy - Sell"
                    }
                },
                {
                    "id": "output-1",
                    "type": "output",
                    "position": {"x": 1130, "y": 150},
                    "data": {
                        "label": "Position"
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "signal-1", "target": "slice-1", "targetHandle": "input"},
                {"id": "e2", "source": "signal-1", "target": "slice-2", "targetHandle": "input"},
                {"id": "e3", "source": "slice-1", "target": "mean-1", "targetHandle": "input"},
                {"id": "e4", "source": "slice-2", "target": "mean-2", "targetHandle": "input"},
                {"id": "e5", "source": "mean-2", "sourceHandle": "value", "target": "crossover-1", "targetHandle": "fast"},
                {"id": "e6", "source": "mean-1", "sourceHandle": "value", "target": "crossover-1", "targetHandle": "slow"},
                {"id": "e7", "source": "crossover-1", "sourceHandle": "cross_above", "target": "subtract-1", "targetHandle": "a"},
                {"id": "e8", "source": "crossover-1", "sourceHandle": "cross_below", "target": "subtract-1", "targetHandle": "b"},
                {"id": "e9", "source": "subtract-1", "target": "output-1", "targetHandle": "input"}
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 1}
        }
    },
    
    "rsi_mean_reversion": {
        "name": "RSI Mean Reversion",
        "description": "Buy when RSI falls below 30 (oversold), sell when RSI rises above 70 (overbought). Classic mean reversion strategy.",
        "symbol": "SPY",
        "primary_timespan": "day",
        "primary_multiplier": 1,
        "graph": {
            "nodes": [
                {
                    "id": "signal-1",
                    "type": "signal",
                    "position": {"x": 50, "y": 150},
                    "data": {
                        "label": "Price",
                        "signalId": "SPY_day_close",
                        "description": "SPY daily close"
                    }
                },
                {
                    "id": "slice-1",
                    "type": "slice",
                    "position": {"x": 260, "y": 150},
                    "data": {
                        "label": "Last 30",
                        "n": 30
                    }
                },
                {
                    "id": "rsi-1",
                    "type": "rsi",
                    "position": {"x": 470, "y": 150},
                    "data": {
                        "label": "RSI (14)",
                        "period": 14
                    }
                },
                {
                    "id": "slice-2",
                    "type": "slice",
                    "position": {"x": 680, "y": 150},
                    "data": {
                        "label": "Latest RSI",
                        "n": 1
                    }
                },
                {
                    "id": "threshold-1",
                    "type": "threshold",
                    "position": {"x": 890, "y": 50},
                    "data": {
                        "label": "Oversold (<30)",
                        "threshold": 30,
                        "mode": "below"
                    }
                },
                {
                    "id": "threshold-2",
                    "type": "threshold",
                    "position": {"x": 890, "y": 250},
                    "data": {
                        "label": "Overbought (>70)",
                        "threshold": 70,
                        "mode": "above"
                    }
                },
                {
                    "id": "subtract-1",
                    "type": "subtract",
                    "position": {"x": 1100, "y": 150},
                    "data": {
                        "label": "Buy - Sell"
                    }
                },
                {
                    "id": "output-1",
                    "type": "output",
                    "position": {"x": 1310, "y": 150},
                    "data": {
                        "label": "Position"
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "signal-1", "target": "slice-1", "targetHandle": "input"},
                {"id": "e2", "source": "slice-1", "target": "rsi-1", "targetHandle": "input"},
                {"id": "e3", "source": "rsi-1", "target": "slice-2", "targetHandle": "input"},
                {"id": "e4", "source": "slice-2", "target": "threshold-1", "targetHandle": "input"},
                {"id": "e5", "source": "slice-2", "target": "threshold-2", "targetHandle": "input"},
                {"id": "e6", "source": "threshold-1", "target": "subtract-1", "targetHandle": "a"},
                {"id": "e7", "source": "threshold-2", "target": "subtract-1", "targetHandle": "b"},
                {"id": "e8", "source": "subtract-1", "target": "output-1", "targetHandle": "input"}
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 1}
        }
    },
    
    "bollinger_mean_reversion": {
        "name": "Bollinger Band Mean Reversion",
        "description": "Buy when price touches lower Bollinger Band, sell when price touches upper band. Uses 20-period SMA with 2 std dev bands.",
        "symbol": "QQQ",
        "primary_timespan": "day",
        "primary_multiplier": 1,
        "graph": {
            "nodes": [
                {
                    "id": "signal-1",
                    "type": "signal",
                    "position": {"x": 50, "y": 180},
                    "data": {
                        "label": "Price",
                        "signalId": "QQQ_day_close",
                        "description": "QQQ daily close"
                    }
                },
                {
                    "id": "slice-1",
                    "type": "slice",
                    "position": {"x": 260, "y": 180},
                    "data": {
                        "label": "Last 30",
                        "n": 30
                    }
                },
                {
                    "id": "bollinger-1",
                    "type": "bollinger",
                    "position": {"x": 470, "y": 180},
                    "data": {
                        "label": "Bollinger",
                        "period": 20,
                        "stdDev": 2
                    }
                },
                {
                    "id": "slice-upper",
                    "type": "slice",
                    "position": {"x": 680, "y": 50},
                    "data": {
                        "label": "Upper",
                        "n": 1
                    }
                },
                {
                    "id": "slice-lower",
                    "type": "slice",
                    "position": {"x": 680, "y": 310},
                    "data": {
                        "label": "Lower",
                        "n": 1
                    }
                },
                {
                    "id": "slice-price",
                    "type": "slice",
                    "position": {"x": 680, "y": 180},
                    "data": {
                        "label": "Current Price",
                        "n": 1
                    }
                },
                {
                    "id": "compare-1",
                    "type": "compare",
                    "position": {"x": 920, "y": 50},
                    "data": {
                        "label": "Price > Upper",
                        "compareOp": "gt"
                    }
                },
                {
                    "id": "compare-2",
                    "type": "compare",
                    "position": {"x": 920, "y": 310},
                    "data": {
                        "label": "Price < Lower",
                        "compareOp": "lt"
                    }
                },
                {
                    "id": "subtract-1",
                    "type": "subtract",
                    "position": {"x": 1130, "y": 180},
                    "data": {
                        "label": "Buy - Sell"
                    }
                },
                {
                    "id": "output-1",
                    "type": "output",
                    "position": {"x": 1340, "y": 180},
                    "data": {
                        "label": "Position"
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "signal-1", "target": "slice-1", "targetHandle": "input"},
                {"id": "e2", "source": "slice-1", "target": "bollinger-1", "targetHandle": "input"},
                {"id": "e3", "source": "bollinger-1", "sourceHandle": "upper", "target": "slice-upper", "targetHandle": "input"},
                {"id": "e4", "source": "bollinger-1", "sourceHandle": "lower", "target": "slice-lower", "targetHandle": "input"},
                {"id": "e5", "source": "slice-1", "target": "slice-price", "targetHandle": "input"},
                {"id": "e6", "source": "slice-price", "target": "compare-1", "targetHandle": "a"},
                {"id": "e7", "source": "slice-upper", "target": "compare-1", "targetHandle": "b"},
                {"id": "e8", "source": "slice-price", "target": "compare-2", "targetHandle": "a"},
                {"id": "e9", "source": "slice-lower", "target": "compare-2", "targetHandle": "b"},
                {"id": "e10", "source": "compare-2", "target": "subtract-1", "targetHandle": "a"},
                {"id": "e11", "source": "compare-1", "target": "subtract-1", "targetHandle": "b"},
                {"id": "e12", "source": "subtract-1", "target": "output-1", "targetHandle": "input"}
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 0.9}
        }
    },
    
    "macd_crossover": {
        "name": "MACD Signal Crossover",
        "description": "Buy when MACD line crosses above signal line, sell when it crosses below. Uses standard 12/26/9 periods.",
        "symbol": "MSFT",
        "primary_timespan": "day",
        "primary_multiplier": 1,
        "graph": {
            "nodes": [
                {
                    "id": "signal-1",
                    "type": "signal",
                    "position": {"x": 50, "y": 150},
                    "data": {
                        "label": "Price",
                        "signalId": "MSFT_day_close",
                        "description": "MSFT daily close"
                    }
                },
                {
                    "id": "slice-1",
                    "type": "slice",
                    "position": {"x": 260, "y": 150},
                    "data": {
                        "label": "Last 50",
                        "n": 50
                    }
                },
                {
                    "id": "macd-1",
                    "type": "macd",
                    "position": {"x": 470, "y": 150},
                    "data": {
                        "label": "MACD",
                        "fastPeriod": 12,
                        "slowPeriod": 26,
                        "signalPeriod": 9
                    }
                },
                {
                    "id": "slice-macd",
                    "type": "slice",
                    "position": {"x": 680, "y": 50},
                    "data": {
                        "label": "MACD Line",
                        "n": 1
                    }
                },
                {
                    "id": "slice-signal",
                    "type": "slice",
                    "position": {"x": 680, "y": 250},
                    "data": {
                        "label": "Signal Line",
                        "n": 1
                    }
                },
                {
                    "id": "crossover-1",
                    "type": "crossover",
                    "position": {"x": 920, "y": 150},
                    "data": {
                        "label": "MACD Crossover"
                    }
                },
                {
                    "id": "subtract-1",
                    "type": "subtract",
                    "position": {"x": 1130, "y": 150},
                    "data": {
                        "label": "Buy - Sell"
                    }
                },
                {
                    "id": "output-1",
                    "type": "output",
                    "position": {"x": 1340, "y": 150},
                    "data": {
                        "label": "Position"
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "signal-1", "target": "slice-1", "targetHandle": "input"},
                {"id": "e2", "source": "slice-1", "target": "macd-1", "targetHandle": "input"},
                {"id": "e3", "source": "macd-1", "sourceHandle": "macd", "target": "slice-macd", "targetHandle": "input"},
                {"id": "e4", "source": "macd-1", "sourceHandle": "signal", "target": "slice-signal", "targetHandle": "input"},
                {"id": "e5", "source": "slice-macd", "target": "crossover-1", "targetHandle": "fast"},
                {"id": "e6", "source": "slice-signal", "target": "crossover-1", "targetHandle": "slow"},
                {"id": "e7", "source": "crossover-1", "sourceHandle": "cross_above", "target": "subtract-1", "targetHandle": "a"},
                {"id": "e8", "source": "crossover-1", "sourceHandle": "cross_below", "target": "subtract-1", "targetHandle": "b"},
                {"id": "e9", "source": "subtract-1", "target": "output-1", "targetHandle": "input"}
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 0.95}
        }
    },
    
    "momentum_roc": {
        "name": "Momentum (Rate of Change)",
        "description": "Buy when price momentum is positive (price rising), sell when negative. Uses 10-day rate of change.",
        "symbol": "NVDA",
        "primary_timespan": "day",
        "primary_multiplier": 1,
        "graph": {
            "nodes": [
                {
                    "id": "signal-1",
                    "type": "signal",
                    "position": {"x": 50, "y": 150},
                    "data": {
                        "label": "Price",
                        "signalId": "NVDA_day_close",
                        "description": "NVDA daily close"
                    }
                },
                {
                    "id": "slice-1",
                    "type": "slice",
                    "position": {"x": 260, "y": 150},
                    "data": {
                        "label": "Last 20",
                        "n": 20
                    }
                },
                {
                    "id": "shift_diff-1",
                    "type": "shift_diff",
                    "position": {"x": 470, "y": 150},
                    "data": {
                        "label": "10-day ROC",
                        "n": 10
                    }
                },
                {
                    "id": "slice-2",
                    "type": "slice",
                    "position": {"x": 680, "y": 150},
                    "data": {
                        "label": "Latest ROC",
                        "n": 1
                    }
                },
                {
                    "id": "threshold-1",
                    "type": "threshold",
                    "position": {"x": 890, "y": 50},
                    "data": {
                        "label": "Positive (>0.01)",
                        "threshold": 0.01,
                        "mode": "above"
                    }
                },
                {
                    "id": "threshold-2",
                    "type": "threshold",
                    "position": {"x": 890, "y": 250},
                    "data": {
                        "label": "Negative (<-0.01)",
                        "threshold": -0.01,
                        "mode": "below"
                    }
                },
                {
                    "id": "subtract-1",
                    "type": "subtract",
                    "position": {"x": 1100, "y": 150},
                    "data": {
                        "label": "Buy - Sell"
                    }
                },
                {
                    "id": "output-1",
                    "type": "output",
                    "position": {"x": 1310, "y": 150},
                    "data": {
                        "label": "Position"
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "signal-1", "target": "slice-1", "targetHandle": "input"},
                {"id": "e2", "source": "slice-1", "target": "shift_diff-1", "targetHandle": "input"},
                {"id": "e3", "source": "shift_diff-1", "target": "slice-2", "targetHandle": "input"},
                {"id": "e4", "source": "slice-2", "target": "threshold-1", "targetHandle": "input"},
                {"id": "e5", "source": "slice-2", "target": "threshold-2", "targetHandle": "input"},
                {"id": "e6", "source": "threshold-1", "target": "subtract-1", "targetHandle": "a"},
                {"id": "e7", "source": "threshold-2", "target": "subtract-1", "targetHandle": "b"},
                {"id": "e8", "source": "subtract-1", "target": "output-1", "targetHandle": "input"}
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 1}
        }
    },
    
    "mlp_predictor": {
        "name": "Basic MLP Signal Predictor",
        "description": "A simple 2-layer neural network that predicts position based on recent price features",
        "symbol": "AAPL",
        "primary_timespan": "day",
        "primary_multiplier": 1,
        "graph": {
            "nodes": [
                {
                    "id": "signal-1",
                    "type": "signal",
                    "position": {"x": 65, "y": 120},
                    "data": {
                        "label": "Price Signal",
                        "signalId": "AAPL_day_close"
                    }
                },
                {
                    "id": "slice-1",
                    "type": "slice",
                    "position": {"x": 325, "y": 120},
                    "data": {
                        "label": "Last 10 bars",
                        "n": 10
                    }
                },
                {
                    "id": "normalize-1",
                    "type": "normalize",
                    "position": {"x": 585, "y": 120},
                    "data": {
                        "label": "Normalize"
                    }
                },
                {
                    "id": "linear-1",
                    "type": "linear",
                    "position": {"x": 845, "y": 120},
                    "data": {
                        "label": "Hidden Layer",
                        "name": "hidden1",
                        "inFeatures": 10,
                        "outFeatures": 8
                    }
                },
                {
                    "id": "relu-1",
                    "type": "relu",
                    "position": {"x": 1105, "y": 120},
                    "data": {
                        "label": "ReLU"
                    }
                },
                {
                    "id": "linear-2",
                    "type": "linear",
                    "position": {"x": 1365, "y": 120},
                    "data": {
                        "label": "Output Layer",
                        "name": "output_layer",
                        "inFeatures": 8,
                        "outFeatures": 1
                    }
                },
                {
                    "id": "tanh-1",
                    "type": "tanh",
                    "position": {"x": 1625, "y": 120},
                    "data": {
                        "label": "Tanh (scale to [-1,1])"
                    }
                },
                {
                    "id": "output-1",
                    "type": "output",
                    "position": {"x": 1885, "y": 120},
                    "data": {
                        "label": "Position Delta"
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "signal-1", "target": "slice-1", "targetHandle": "input"},
                {"id": "e2", "source": "slice-1", "target": "normalize-1", "targetHandle": "input"},
                {"id": "e3", "source": "normalize-1", "target": "linear-1", "targetHandle": "input"},
                {"id": "e4", "source": "linear-1", "target": "relu-1", "targetHandle": "input"},
                {"id": "e5", "source": "relu-1", "target": "linear-2", "targetHandle": "input"},
                {"id": "e6", "source": "linear-2", "target": "tanh-1", "targetHandle": "input"},
                {"id": "e7", "source": "tanh-1", "target": "output-1", "targetHandle": "input"}
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 0.8}
        }
    },
    
    "lstm_sequence": {
        "name": "LSTM Sequence Model",
        "description": "An LSTM-based model for sequence prediction (placeholder - LSTM not fully implemented)",
        "symbol": "AAPL",
        "primary_timespan": "hour",
        "primary_multiplier": 1,
        "graph": {
            "nodes": [
                {
                    "id": "signal-1",
                    "type": "signal",
                    "position": {"x": 65, "y": 120},
                    "data": {
                        "label": "Price Signal",
                        "signalId": "AAPL_hour_close"
                    }
                },
                {
                    "id": "slice-1",
                    "type": "slice",
                    "position": {"x": 325, "y": 120},
                    "data": {
                        "label": "Sequence (20 bars)",
                        "n": 20
                    }
                },
                {
                    "id": "normalize-1",
                    "type": "normalize",
                    "position": {"x": 585, "y": 120},
                    "data": {
                        "label": "Normalize"
                    }
                },
                {
                    "id": "rolling_mean-1",
                    "type": "rolling_mean",
                    "position": {"x": 845, "y": 40},
                    "data": {
                        "label": "Rolling Mean (5)",
                        "window": 5
                    }
                },
                {
                    "id": "rolling_std-1",
                    "type": "rolling_std",
                    "position": {"x": 845, "y": 200},
                    "data": {
                        "label": "Rolling Std (5)",
                        "window": 5
                    }
                },
                {
                    "id": "subtract-1",
                    "type": "subtract",
                    "position": {"x": 1105, "y": 120},
                    "data": {
                        "label": "Mean - Std"
                    }
                },
                {
                    "id": "mean-1",
                    "type": "mean",
                    "position": {"x": 1365, "y": 120},
                    "data": {
                        "label": "Average",
                        "axis": None
                    }
                },
                {
                    "id": "clip-1",
                    "type": "clip",
                    "position": {"x": 1625, "y": 120},
                    "data": {
                        "label": "Clip",
                        "min": -1,
                        "max": 1
                    }
                },
                {
                    "id": "output-1",
                    "type": "output",
                    "position": {"x": 1885, "y": 120},
                    "data": {
                        "label": "Position Delta"
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "signal-1", "target": "slice-1", "targetHandle": "input"},
                {"id": "e2", "source": "slice-1", "target": "normalize-1", "targetHandle": "input"},
                {"id": "e3", "source": "normalize-1", "target": "rolling_mean-1", "targetHandle": "input"},
                {"id": "e4", "source": "normalize-1", "target": "rolling_std-1", "targetHandle": "input"},
                {"id": "e5", "source": "rolling_mean-1", "target": "subtract-1", "targetHandle": "a"},
                {"id": "e6", "source": "rolling_std-1", "target": "subtract-1", "targetHandle": "b"},
                {"id": "e7", "source": "subtract-1", "target": "mean-1", "targetHandle": "input"},
                {"id": "e8", "source": "mean-1", "target": "clip-1", "targetHandle": "input"},
                {"id": "e9", "source": "clip-1", "target": "output-1", "targetHandle": "input"}
            ],
            "viewport": {"x": 0, "y": 0, "zoom": 0.8}
        }
    }
}


def get_templates() -> List[Dict]:
    """Get list of all available templates with metadata."""
    return [
        {
            "name": key,
            "title": template["name"],
            "description": template["description"],
            "symbol": template["symbol"],
            "timespan": template["primary_timespan"],
        }
        for key, template in TEMPLATES.items()
    ]


def get_template(name: str) -> Optional[Dict]:
    """Get a specific template by name."""
    return TEMPLATES.get(name)
