"""Design templates for Visual Agent Designer.

Pre-built templates for common trading strategies.
"""

from typing import Dict, List, Optional


# Template definitions
TEMPLATES = {
    "sma_crossover": {
        "name": "Simple Moving Average Crossover",
        "description": "Buy when fast SMA crosses above slow SMA, sell when it crosses below",
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
                        "signalId": "AAPL_day_close",
                        "description": "Daily close price"
                    }
                },
                {
                    "id": "slice-1",
                    "type": "slice",
                    "position": {"x": 325, "y": 40},
                    "data": {
                        "label": "Last 50 bars",
                        "n": 50
                    }
                },
                {
                    "id": "slice-2",
                    "type": "slice",
                    "position": {"x": 325, "y": 200},
                    "data": {
                        "label": "Last 20 bars",
                        "n": 20
                    }
                },
                {
                    "id": "mean-1",
                    "type": "mean",
                    "position": {"x": 585, "y": 40},
                    "data": {
                        "label": "Slow SMA (50)",
                        "axis": None
                    }
                },
                {
                    "id": "mean-2",
                    "type": "mean",
                    "position": {"x": 585, "y": 200},
                    "data": {
                        "label": "Fast SMA (20)",
                        "axis": None
                    }
                },
                {
                    "id": "subtract-1",
                    "type": "subtract",
                    "position": {"x": 845, "y": 120},
                    "data": {
                        "label": "Fast - Slow"
                    }
                },
                {
                    "id": "clip-1",
                    "type": "clip",
                    "position": {"x": 1105, "y": 120},
                    "data": {
                        "label": "Clip to [-1, 1]",
                        "min": -1,
                        "max": 1
                    }
                },
                {
                    "id": "output-1",
                    "type": "output",
                    "position": {"x": 1365, "y": 120},
                    "data": {
                        "label": "Position Delta"
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "signal-1", "target": "slice-1", "targetHandle": "input"},
                {"id": "e2", "source": "signal-1", "target": "slice-2", "targetHandle": "input"},
                {"id": "e3", "source": "slice-1", "target": "mean-1", "targetHandle": "input"},
                {"id": "e4", "source": "slice-2", "target": "mean-2", "targetHandle": "input"},
                {"id": "e5", "source": "mean-2", "target": "subtract-1", "targetHandle": "a"},
                {"id": "e6", "source": "mean-1", "target": "subtract-1", "targetHandle": "b"},
                {"id": "e7", "source": "subtract-1", "target": "clip-1", "targetHandle": "input"},
                {"id": "e8", "source": "clip-1", "target": "output-1", "targetHandle": "input"}
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
