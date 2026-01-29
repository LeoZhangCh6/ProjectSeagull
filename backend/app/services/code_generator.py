"""Code generator for visual agent designs.

Converts a visual graph (nodes + edges) into executable Python agent code.
"""

from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
from app.models.schemas import CodeGenerationResponse


# Node type definitions with their input/output ports
NODE_TYPES = {
    # Data sources
    "signal": {
        "inputs": [],
        "outputs": ["value"],
        "category": "data",
    },
    "constant": {
        "inputs": [],
        "outputs": ["value"],
        "category": "data",
    },
    "variable": {
        "inputs": [],
        "outputs": ["value"],
        "category": "data",
    },
    
    # Operations
    "slice": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "operation",
    },
    "concat": {
        "inputs": ["input1", "input2"],
        "outputs": ["output"],
        "category": "operation",
    },
    "add": {
        "inputs": ["a", "b"],
        "outputs": ["output"],
        "category": "operation",
    },
    "subtract": {
        "inputs": ["a", "b"],
        "outputs": ["output"],
        "category": "operation",
    },
    "multiply": {
        "inputs": ["a", "b"],
        "outputs": ["output"],
        "category": "operation",
    },
    "divide": {
        "inputs": ["a", "b"],
        "outputs": ["output"],
        "category": "operation",
    },
    "matmul": {
        "inputs": ["a", "b"],
        "outputs": ["output"],
        "category": "operation",
    },
    "mean": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "operation",
    },
    "sum": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "operation",
    },
    "std": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "operation",
    },
    "min": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "operation",
    },
    "max": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "operation",
    },
    "normalize": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "operation",
    },
    "clip": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "operation",
    },
    
    # Technical indicators
    "rolling_mean": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "indicator",
    },
    "rolling_std": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "indicator",
    },
    "rsi": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "indicator",
    },
    "macd": {
        "inputs": ["input"],
        "outputs": ["macd", "signal", "histogram"],
        "category": "indicator",
    },
    "bollinger": {
        "inputs": ["input"],
        "outputs": ["upper", "middle", "lower"],
        "category": "indicator",
    },
    
    # ML layers (Phase 2)
    "linear": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "ml",
    },
    "relu": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "ml",
    },
    "tanh": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "ml",
    },
    "sigmoid": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "ml",
    },
    "softmax": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "ml",
    },
    "lstm": {
        "inputs": ["input"],
        "outputs": ["output", "hidden"],
        "category": "ml",
    },
    "conv1d": {
        "inputs": ["input"],
        "outputs": ["output"],
        "category": "ml",
    },
    
    # Output
    "output": {
        "inputs": ["input"],
        "outputs": [],
        "category": "output",
    },
}


def topological_sort(nodes: List[Dict], edges: List[Dict]) -> Tuple[List[str], List[str]]:
    """
    Sort nodes in topological order (dependencies first).
    Returns (sorted_node_ids, errors).
    """
    # Build adjacency list
    in_degree = defaultdict(int)
    adjacency = defaultdict(list)
    node_ids = {n["id"] for n in nodes}
    
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source in node_ids and target in node_ids:
            adjacency[source].append(target)
            in_degree[target] += 1
    
    # Initialize with nodes that have no incoming edges
    queue = [n["id"] for n in nodes if in_degree[n["id"]] == 0]
    sorted_nodes = []
    
    while queue:
        node_id = queue.pop(0)
        sorted_nodes.append(node_id)
        
        for neighbor in adjacency[node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    errors = []
    if len(sorted_nodes) != len(nodes):
        errors.append("Graph contains a cycle")
    
    return sorted_nodes, errors


def generate_node_code(node: Dict, input_vars: Dict[str, str]) -> Tuple[str, str, List[str]]:
    """
    Generate Python code for a single node.
    Returns (output_var_name, code_line, errors).
    """
    node_id = node["id"]
    node_type = node.get("type", "unknown")
    data = node.get("data", {})
    errors = []
    
    # Clean node_id for use as variable name
    var_name = f"node_{node_id.replace('-', '_')}"
    
    if node_type == "signal":
        signal_id = data.get("signalId", "unknown")
        code = f'{var_name} = self._get_signal("{signal_id}", history)'
        return var_name, code, errors
    
    elif node_type == "constant":
        value = data.get("value", 0)
        shape = data.get("shape", [1])
        if isinstance(shape, list) and len(shape) > 1:
            code = f'{var_name} = torch.full({tuple(shape)}, {value}, dtype=torch.float32)'
        else:
            code = f'{var_name} = torch.tensor({value}, dtype=torch.float32)'
        return var_name, code, errors
    
    elif node_type == "variable":
        shape = data.get("shape", [1])
        init_type = data.get("initType", "random")  # "random", "zeros", "ones"
        name = data.get("name", var_name)
        
        if init_type == "zeros":
            init_code = f"torch.zeros({tuple(shape)}, dtype=torch.float32)"
        elif init_type == "ones":
            init_code = f"torch.ones({tuple(shape)}, dtype=torch.float32)"
        else:  # random
            init_code = f"torch.randn({tuple(shape)}, dtype=torch.float32) * 0.01"
        
        code = f'{var_name} = self._get_or_init_param("{name}", lambda: {init_code})'
        return var_name, code, errors
    
    elif node_type == "slice":
        input_var = input_vars.get("input", "None")
        n = data.get("n", 10)
        code = f'{var_name} = {input_var}[-{n}:] if len({input_var}) >= {n} else {input_var}'
        return var_name, code, errors
    
    elif node_type == "concat":
        input1 = input_vars.get("input1", "None")
        input2 = input_vars.get("input2", "None")
        axis = data.get("axis", 0)
        code = f'{var_name} = torch.cat([torch.as_tensor({input1}), torch.as_tensor({input2})], dim={axis})'
        return var_name, code, errors
    
    elif node_type in ["add", "subtract", "multiply", "divide"]:
        a = input_vars.get("a", "0")
        b = input_vars.get("b", "0")
        ops = {"add": "+", "subtract": "-", "multiply": "*", "divide": "/"}
        code = f'{var_name} = torch.as_tensor({a}) {ops[node_type]} torch.as_tensor({b})'
        return var_name, code, errors
    
    elif node_type == "matmul":
        a = input_vars.get("a", "None")
        b = input_vars.get("b", "None")
        code = f'{var_name} = torch.matmul(torch.as_tensor({a}, dtype=torch.float32), torch.as_tensor({b}, dtype=torch.float32))'
        return var_name, code, errors
    
    elif node_type in ["mean", "sum", "std", "min", "max"]:
        input_var = input_vars.get("input", "None")
        axis = data.get("axis", None)
        axis_str = f", dim={axis}" if axis is not None else ""
        if node_type == "min":
            code = f'{var_name} = torch.as_tensor({input_var}).min(){".values" if axis is not None else ""}'
        elif node_type == "max":
            code = f'{var_name} = torch.as_tensor({input_var}).max(){".values" if axis is not None else ""}'
        else:
            code = f'{var_name} = torch.as_tensor({input_var}).{node_type}({axis_str})'
        return var_name, code, errors
    
    elif node_type == "normalize":
        input_var = input_vars.get("input", "None")
        code = f'{var_name} = (torch.as_tensor({input_var}) - torch.as_tensor({input_var}).mean()) / (torch.as_tensor({input_var}).std() + 1e-8)'
        return var_name, code, errors
    
    elif node_type == "clip":
        input_var = input_vars.get("input", "None")
        min_val = data.get("min", -float("inf"))
        max_val = data.get("max", float("inf"))
        code = f'{var_name} = torch.clamp(torch.as_tensor({input_var}), {min_val}, {max_val})'
        return var_name, code, errors
    
    elif node_type == "rolling_mean":
        input_var = input_vars.get("input", "None")
        window = data.get("window", 10)
        code = f'{var_name} = self._rolling_mean({input_var}, {window})'
        return var_name, code, errors
    
    elif node_type == "rolling_std":
        input_var = input_vars.get("input", "None")
        window = data.get("window", 10)
        code = f'{var_name} = self._rolling_std({input_var}, {window})'
        return var_name, code, errors
    
    elif node_type == "output":
        input_var = input_vars.get("input", "0")
        code = f'{var_name} = float({input_var})'
        return var_name, code, errors
    
    # ML layers
    elif node_type == "linear":
        input_var = input_vars.get("input", "None")
        in_features = data.get("inFeatures", 10)
        out_features = data.get("outFeatures", 1)
        layer_name = data.get("name", f"linear_{node_id}")
        code = f'{var_name} = self._get_or_init_layer("{layer_name}", lambda: torch.nn.Linear({in_features}, {out_features}))(torch.as_tensor({input_var}, dtype=torch.float32))'
        return var_name, code, errors
    
    elif node_type in ["relu", "tanh", "sigmoid", "softmax"]:
        input_var = input_vars.get("input", "None")
        activation_fn = {
            "relu": "torch.relu",
            "tanh": "torch.tanh",
            "sigmoid": "torch.sigmoid",
            "softmax": "torch.softmax",
        }
        if node_type == "softmax":
            code = f'{var_name} = {activation_fn[node_type]}(torch.as_tensor({input_var}, dtype=torch.float32), dim=-1)'
        else:
            code = f'{var_name} = {activation_fn[node_type]}(torch.as_tensor({input_var}, dtype=torch.float32))'
        return var_name, code, errors
    
    else:
        errors.append(f"Unknown node type: {node_type}")
        code = f'{var_name} = None  # Unknown type: {node_type}'
        return var_name, code, errors


def generate_agent_code(
    graph: Dict,
    symbol: str = "AAPL",
    primary_timespan: str = "day",
    primary_multiplier: int = 1,
) -> CodeGenerationResponse:
    """
    Generate complete Python agent code from a visual design graph.
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    errors = []
    warnings = []
    
    if not nodes:
        return CodeGenerationResponse(
            code="",
            errors=["Graph has no nodes"],
            warnings=[],
        )
    
    # Check for output node
    output_nodes = [n for n in nodes if n.get("type") == "output"]
    if not output_nodes:
        errors.append("Graph must have an output node")
    
    # Topological sort
    sorted_ids, sort_errors = topological_sort(nodes, edges)
    errors.extend(sort_errors)
    
    if errors:
        return CodeGenerationResponse(code="", errors=errors, warnings=warnings)
    
    # Build node lookup and edge lookup
    node_map = {n["id"]: n for n in nodes}
    
    # Map: target_node_id -> { target_handle -> source_var }
    incoming_edges: Dict[str, Dict[str, str]] = defaultdict(dict)
    
    # Track output variable names
    output_vars: Dict[str, str] = {}
    
    # Generate code for each node in order
    code_lines = []
    
    for node_id in sorted_ids:
        node = node_map[node_id]
        
        # Gather input variables from incoming edges
        input_vars = {}
        for edge in edges:
            if edge.get("target") == node_id:
                source_id = edge.get("source")
                target_handle = edge.get("targetHandle", "input")
                if source_id in output_vars:
                    input_vars[target_handle] = output_vars[source_id]
        
        var_name, code_line, node_errors = generate_node_code(node, input_vars)
        errors.extend(node_errors)
        
        output_vars[node_id] = var_name
        code_lines.append(code_line)
    
    # Find the output node's variable
    output_var = "0"
    for n in output_nodes:
        if n["id"] in output_vars:
            output_var = output_vars[n["id"]]
            break
    
    # Collect used signals
    signal_ids = []
    for n in nodes:
        if n.get("type") == "signal":
            sig_id = n.get("data", {}).get("signalId")
            if sig_id:
                signal_ids.append(sig_id)
    
    # Generate the full agent class
    agent_code = f'''"""Auto-generated agent from Visual Agent Designer."""

import torch
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any

from ib_backtester.engine import BaseAgent
from ib_backtester.types import Action, Order, OrderType


class VisualDesignAgent(BaseAgent):
    """
    Agent generated from visual design.
    
    Symbol: {symbol}
    Frequency: {primary_timespan} x {primary_multiplier}
    """
    
    def __init__(self) -> None:
        # Trading configuration
        self.symbol = "{symbol}"
        self.primary_timespan = "{primary_timespan}"
        self.primary_multiplier = {primary_multiplier}
        
        # Signal requirements
        self.used_signal_ids = {signal_ids!r}
        
        # Parameters and layers (for ML nodes)
        self._params: Dict[str, torch.Tensor] = {{}}
        self._layers: Dict[str, torch.nn.Module] = {{}}
        
        # Cache for signal data
        self._signal_cache: Dict[str, Any] = {{}}
    
    def _get_or_init_param(self, name: str, init_fn) -> torch.Tensor:
        """Get or initialize a parameter tensor."""
        if name not in self._params:
            self._params[name] = init_fn()
        return self._params[name]
    
    def _get_or_init_layer(self, name: str, init_fn) -> torch.nn.Module:
        """Get or initialize an ML layer."""
        if name not in self._layers:
            self._layers[name] = init_fn()
        return self._layers[name]
    
    def _get_signal(self, signal_id: str, history: pd.DataFrame) -> torch.Tensor:
        """Get signal data as tensor."""
        # For now, use close price from history as placeholder
        # In production, this would fetch from the signal registry
        if "close" in history.columns:
            return torch.tensor(history["close"].values, dtype=torch.float32)
        return torch.zeros(len(history), dtype=torch.float32)
    
    def _rolling_mean(self, data, window: int) -> torch.Tensor:
        """Compute rolling mean."""
        t = torch.as_tensor(data, dtype=torch.float32)
        if len(t) < window:
            return t.mean().unsqueeze(0)
        return torch.tensor([t[max(0,i-window+1):i+1].mean().item() for i in range(len(t))], dtype=torch.float32)
    
    def _rolling_std(self, data, window: int) -> torch.Tensor:
        """Compute rolling standard deviation."""
        t = torch.as_tensor(data, dtype=torch.float32)
        if len(t) < window:
            return t.std().unsqueeze(0)
        return torch.tensor([t[max(0,i-window+1):i+1].std().item() for i in range(len(t))], dtype=torch.float32)
    
    def on_start(self, ib, contract) -> None:
        """Called at simulation start."""
        pass
    
    def on_bar(self, ib, contract, history: pd.DataFrame) -> None:
        """Called on each bar - execute the visual design logic."""
        if history.empty:
            return
        
        # Get current state
        state = ib.get_portfolio_state()
        price = float(history["close"].iloc[-1])
        
        # Execute the generated computation graph
        try:
{chr(10).join("            " + line for line in code_lines)}
            
            # Get the final output (position delta)
            delta = int(round({output_var}))
            
            # Apply risk limits
            if delta > 0:
                max_afford = int(state["cash"] // max(price, 1e-9))
                delta = min(delta, max_afford)
            elif delta < 0:
                delta = -min(abs(delta), int(state["position"]))
            
            # Execute trade if non-zero
            if delta != 0:
                oid = ib.nextOrderId()
                if delta > 0:
                    ib.placeOrder(oid, contract, Order(action=Action.BUY, totalQuantity=abs(delta), orderType=OrderType.MKT))
                else:
                    ib.placeOrder(oid, contract, Order(action=Action.SELL, totalQuantity=abs(delta), orderType=OrderType.MKT))
        
        except Exception as e:
            # Log error but don't crash
            print(f"[VisualDesignAgent] Error in computation: {{e}}")
    
    def on_end(self, ib, contract) -> None:
        """Called at simulation end."""
        pass


def create_agent() -> BaseAgent:
    """Factory function for agent loading system."""
    return VisualDesignAgent()
'''
    
    return CodeGenerationResponse(
        code=agent_code,
        errors=errors,
        warnings=warnings,
    )
