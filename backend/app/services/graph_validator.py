"""Graph validator for visual agent designs.

Validates node connections, dimension compatibility, and detects cycles.
"""

from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from app.models.schemas import ValidationResult


# Node type definitions with dimension rules
NODE_DIMENSION_RULES = {
    "signal": {
        "inputs": {},
        "output_dim": lambda data, inputs: ["T"],  # Time series, length T
    },
    "constant": {
        "inputs": {},
        "output_dim": lambda data, inputs: data.get("shape", [1]),
    },
    "variable": {
        "inputs": {},
        "output_dim": lambda data, inputs: data.get("shape", [1]),
    },
    "range": {
        "inputs": {},
        "output_dim": lambda data, inputs: [data.get("n", 10)],
    },
    "agent_state": {
        "inputs": {},
        "output_dim": lambda data, inputs: ["scalar"],  # Outputs 3 scalars
    },
    "agent_equity_curve": {
        "inputs": {},
        "output_dim": lambda data, inputs: [data.get("historyLength", 50)],
    },
    "custom_state": {
        "inputs": {"new_value": "optional"},
        "output_dim": lambda data, inputs: data.get("shape", [1]),
    },
    "sign": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "sin": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "cos": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "slice": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: [data.get("n", 10) - data.get("m", 0)],
    },
    "concat": {
        "inputs": {},  # Dynamic inputs based on numInputs
        "output_dim": lambda data, inputs: ["N", "L"],  # (numInputs, L) matrix
    },
    "transpose": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: ["transposed"],
    },
    "add": {
        "inputs": {"a": "any", "b": "broadcast"},
        "output_dim": lambda data, inputs: inputs.get("a", ["scalar"]),
    },
    "subtract": {
        "inputs": {"a": "any", "b": "broadcast"},
        "output_dim": lambda data, inputs: inputs.get("a", ["scalar"]),
    },
    "multiply": {
        "inputs": {"a": "any", "b": "broadcast"},
        "output_dim": lambda data, inputs: inputs.get("a", ["scalar"]),
    },
    "divide": {
        "inputs": {"a": "any", "b": "broadcast"},
        "output_dim": lambda data, inputs: inputs.get("a", ["scalar"]),
    },
    "matmul": {
        "inputs": {"a": "matrix", "b": "matrix"},
        "output_dim": lambda data, inputs: ["matmul"],  # Result of matrix multiply
    },
    "mean": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: ["scalar"],
    },
    "sum": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: ["scalar"],
    },
    "std": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: ["scalar"],
    },
    "variance": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: ["scalar"],
    },
    "min": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: ["scalar"],
    },
    "max": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: ["scalar"],
    },
    "normalize": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "clip": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "rolling_mean": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "rolling_std": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "shift": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: ["T-n"] if data.get("fillMode", "none") == "none" else inputs.get("input", ["T"]),
    },
    "shift_diff": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: ["T-n"],  # Output is shorter by n elements
    },
    "conv1d_custom": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]) if data.get("padding") == "same" else ["T-k+1"],
    },
    "linear": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: [data.get("outFeatures", 1)],
    },
    "relu": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "tanh": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "sigmoid": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "softmax": {
        "inputs": {"input": "any"},
        "output_dim": lambda data, inputs: inputs.get("input", ["T"]),
    },
    "output": {
        "inputs": {"input": "scalar"},
        "output_dim": lambda data, inputs: ["scalar"],
    },
}


def detect_cycle(nodes: List[Dict], edges: List[Dict]) -> Tuple[bool, Optional[List[str]]]:
    """
    Detect if the graph has a cycle using DFS.
    Returns (has_cycle, cycle_path).
    """
    node_ids = {n["id"] for n in nodes}
    adjacency = defaultdict(list)
    
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source in node_ids and target in node_ids:
            adjacency[source].append(target)
    
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n["id"]: WHITE for n in nodes}
    parent = {}
    
    def dfs(node_id: str) -> Optional[List[str]]:
        color[node_id] = GRAY
        
        for neighbor in adjacency[node_id]:
            if color[neighbor] == GRAY:
                # Found cycle, reconstruct path
                cycle = [neighbor, node_id]
                current = node_id
                while parent.get(current) and parent[current] != neighbor:
                    current = parent[current]
                    cycle.append(current)
                return cycle[::-1]
            elif color[neighbor] == WHITE:
                parent[neighbor] = node_id
                result = dfs(neighbor)
                if result:
                    return result
        
        color[node_id] = BLACK
        return None
    
    for node in nodes:
        if color[node["id"]] == WHITE:
            cycle = dfs(node["id"])
            if cycle:
                return True, cycle
    
    return False, None


def validate_connections(nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
    """
    Validate that all node connections are valid.
    Returns list of errors.
    """
    errors = []
    node_map = {n["id"]: n for n in nodes}
    node_ids = set(node_map.keys())
    
    # Check each edge
    for edge in edges:
        source_id = edge.get("source")
        target_id = edge.get("target")
        
        if source_id not in node_ids:
            errors.append({
                "node_id": source_id,
                "message": f"Edge references non-existent source node: {source_id}"
            })
            continue
        
        if target_id not in node_ids:
            errors.append({
                "node_id": target_id,
                "message": f"Edge references non-existent target node: {target_id}"
            })
            continue
        
        source_node = node_map[source_id]
        target_node = node_map[target_id]
        target_type = target_node.get("type", "unknown")
        target_handle = edge.get("targetHandle", "input")
        
        # Check if target handle is valid for the node type
        if target_type in NODE_DIMENSION_RULES:
            valid_inputs = NODE_DIMENSION_RULES[target_type]["inputs"]
            if target_handle not in valid_inputs and valid_inputs:
                errors.append({
                    "node_id": target_id,
                    "message": f"Invalid input '{target_handle}' for node type '{target_type}'"
                })
    
    return errors


def validate_required_inputs(nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
    """
    Check that all required inputs are connected.
    Returns list of errors.
    """
    errors = []
    node_map = {n["id"]: n for n in nodes}
    
    # Build map of connected inputs for each node
    connected_inputs: Dict[str, set] = defaultdict(set)
    for edge in edges:
        target_id = edge.get("target")
        target_handle = edge.get("targetHandle", "input")
        connected_inputs[target_id].add(target_handle)
    
    # Check each node has required inputs
    for node in nodes:
        node_id = node["id"]
        node_type = node.get("type", "unknown")
        
        if node_type in NODE_DIMENSION_RULES:
            required_inputs = NODE_DIMENSION_RULES[node_type]["inputs"]
            for input_name in required_inputs:
                if input_name not in connected_inputs[node_id]:
                    errors.append({
                        "node_id": node_id,
                        "message": f"Missing required input '{input_name}' for {node_type} node"
                    })
    
    return errors


def compute_dimensions(nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
    """
    Compute output dimensions for each node.
    Returns dict of node_id -> dimension info.
    """
    node_map = {n["id"]: n for n in nodes}
    dimensions = {}
    
    # Build dependency graph
    incoming = defaultdict(dict)  # node_id -> {handle -> source_node_id}
    for edge in edges:
        target_id = edge.get("target")
        source_id = edge.get("source")
        target_handle = edge.get("targetHandle", "input")
        incoming[target_id][target_handle] = source_id
    
    # Topological sort
    in_degree = defaultdict(int)
    adjacency = defaultdict(list)
    
    for edge in edges:
        adjacency[edge["source"]].append(edge["target"])
        in_degree[edge["target"]] += 1
    
    queue = [n["id"] for n in nodes if in_degree[n["id"]] == 0]
    sorted_ids = []
    
    while queue:
        node_id = queue.pop(0)
        sorted_ids.append(node_id)
        for neighbor in adjacency[node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Compute dimensions in order
    for node_id in sorted_ids:
        node = node_map.get(node_id)
        if not node:
            continue
        
        node_type = node.get("type", "unknown")
        data = node.get("data", {})
        
        # Get input dimensions
        input_dims = {}
        for handle, source_id in incoming[node_id].items():
            if source_id in dimensions:
                input_dims[handle] = dimensions[source_id].get("output", ["unknown"])
        
        # Compute output dimension
        if node_type in NODE_DIMENSION_RULES:
            try:
                output_dim = NODE_DIMENSION_RULES[node_type]["output_dim"](data, input_dims)
            except Exception:
                output_dim = ["unknown"]
        else:
            output_dim = ["unknown"]
        
        dimensions[node_id] = {
            "inputs": input_dims,
            "output": output_dim,
        }
    
    return dimensions


def validate_graph(graph: Dict) -> ValidationResult:
    """
    Perform full validation of a visual design graph.
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    errors = []
    warnings = []
    
    # Check for empty graph
    if not nodes:
        return ValidationResult(
            valid=False,
            errors=[{"node_id": None, "message": "Graph has no nodes"}],
            warnings=[],
            node_dimensions={},
        )
    
    # Check for output node
    output_nodes = [n for n in nodes if n.get("type") == "output"]
    if not output_nodes:
        errors.append({"node_id": None, "message": "Graph must have an output node"})
    elif len(output_nodes) > 1:
        warnings.append({"node_id": None, "message": "Graph has multiple output nodes; only the first will be used"})
    
    # Check for cycles
    has_cycle, cycle_path = detect_cycle(nodes, edges)
    if has_cycle:
        errors.append({
            "node_id": cycle_path[0] if cycle_path else None,
            "message": f"Graph contains a cycle: {' -> '.join(cycle_path or [])}"
        })
    
    # Validate connections
    connection_errors = validate_connections(nodes, edges)
    errors.extend(connection_errors)
    
    # Validate required inputs
    input_errors = validate_required_inputs(nodes, edges)
    errors.extend(input_errors)
    
    # Compute dimensions (even if there are errors, for debugging)
    dimensions = compute_dimensions(nodes, edges)
    
    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        node_dimensions=dimensions,
    )
