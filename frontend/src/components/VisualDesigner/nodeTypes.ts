/**
 * Node type definitions for the Visual Agent Designer.
 * Defines all available node types, their inputs/outputs, colors, and default data.
 */

import type { NodeTypeDefinition, VisualNodeType } from '../../types';

// Color palette for different node categories
export const CATEGORY_COLORS = {
  data: '#22c55e',        // Green - data sources
  transform1d: '#3b82f6', // Blue - 1D transformations
  aggregation: '#f59e0b', // Amber - aggregation ops
  transformNd: '#06b6d4', // Cyan - multi-dimension transforms
  ml: '#8b5cf6',          // Purple - ML layers
  output: '#ef4444',      // Red - output
};

// All node type definitions
export const NODE_TYPES: Record<string, NodeTypeDefinition> = {
  // ========== Data Sources ==========
  signal: {
    type: 'signal',
    label: 'Signal',
    category: 'data',
    inputs: [],
    outputs: [{ name: 'value', type: 'tensor' }],
    defaultData: { 
      label: 'Signal',
      signalId: '',
      description: 'Select a signal'
    },
    color: CATEGORY_COLORS.data,
  },
  constant: {
    type: 'constant',
    label: 'Constant',
    category: 'data',
    inputs: [],
    outputs: [{ name: 'value', type: 'tensor' }],
    defaultData: { 
      label: 'Constant',
      value: 0,
      shape: [1]
    },
    color: CATEGORY_COLORS.data,
  },
  variable: {
    type: 'variable',
    label: 'Variable',
    category: 'data',
    inputs: [],
    outputs: [{ name: 'value', type: 'tensor' }],
    defaultData: { 
      label: 'Variable',
      name: 'weight',
      shape: [1],
      initType: 'zeros' // 'random', 'zeros', 'ones'
    },
    color: CATEGORY_COLORS.data,
  },
  range: {
    type: 'range',
    label: 'Range',
    category: 'data',
    inputs: [],
    outputs: [{ name: 'value', type: 'tensor' }],
    defaultData: { 
      label: 'Range',
      n: 10,
      start: 0,
      mode: 'step', // 'step' or 'end'
      step: 1,
      end: 10
    },
    color: CATEGORY_COLORS.data,
  },
  agent_state: {
    type: 'agent_state',
    label: 'Agent State',
    category: 'data',
    inputs: [],
    outputs: [
      { name: 'shares', type: 'scalar' },
      { name: 'equity', type: 'scalar' },
      { name: 'cash', type: 'scalar' }
    ],
    defaultData: { 
      label: 'Agent State',
      demoShares: 10,
      demoEquity: 100000,
    },
    color: CATEGORY_COLORS.data,
  },
  agent_equity_curve: {
    type: 'agent_equity_curve',
    label: 'Equity Curve',
    category: 'data',
    inputs: [],
    outputs: [{ name: 'curve', type: 'tensor' }],
    defaultData: { 
      label: 'Equity Curve',
      historyLength: 50,
      demoEquity: 100000,
    },
    color: CATEGORY_COLORS.data,
  },
  custom_state: {
    type: 'custom_state',
    label: 'Custom State',
    category: 'data',
    inputs: [{ name: 'new_value', type: 'any' }],  // Input to update the state
    outputs: [{ name: 'value', type: 'any' }],     // Output current state value
    defaultData: { 
      label: 'Custom State',
      stateName: 'my_state',
      defaultValue: '0',  // Can be scalar or comma-separated for vector
      shape: [1],  // Shape of the state
    },
    color: CATEGORY_COLORS.data,
  },

  // ========== 1-D Transformations ==========
  slice: {
    type: 'slice',
    label: 'Slice',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Slice',
      n: 10,  // Start from last N
      m: 0    // End at last M (0 = end of array)
    },
    color: CATEGORY_COLORS.transform1d,
  },
  add: {
    type: 'add',
    label: 'Add',
    category: 'transform1d',
    inputs: [
      { name: 'a', type: 'tensor' },
      { name: 'b', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Add (+)' },
    color: CATEGORY_COLORS.transform1d,
  },
  subtract: {
    type: 'subtract',
    label: 'Subtract',
    category: 'transform1d',
    inputs: [
      { name: 'a', type: 'tensor' },
      { name: 'b', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Subtract (-)' },
    color: CATEGORY_COLORS.transform1d,
  },
  multiply: {
    type: 'multiply',
    label: 'Multiply',
    category: 'transform1d',
    inputs: [
      { name: 'a', type: 'tensor' },
      { name: 'b', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Multiply (×)' },
    color: CATEGORY_COLORS.transform1d,
  },
  divide: {
    type: 'divide',
    label: 'Divide',
    category: 'transform1d',
    inputs: [
      { name: 'a', type: 'tensor' },
      { name: 'b', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Divide (÷)' },
    color: CATEGORY_COLORS.transform1d,
  },
  normalize: {
    type: 'normalize',
    label: 'Normalize',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Normalize (z-score)' },
    color: CATEGORY_COLORS.transform1d,
  },
  clip: {
    type: 'clip',
    label: 'Clip',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Clip',
      min: -1,
      max: 1
    },
    color: CATEGORY_COLORS.transform1d,
  },
  rolling_mean: {
    type: 'rolling_mean',
    label: 'Rolling Mean',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Rolling Mean',
      window: 10
    },
    color: CATEGORY_COLORS.transform1d,
  },
  rolling_std: {
    type: 'rolling_std',
    label: 'Rolling Std',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Rolling Std',
      window: 10
    },
    color: CATEGORY_COLORS.transform1d,
  },
  shift: {
    type: 'shift',
    label: 'Shift',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Shift',
      n: 1,
      fillMode: 'none'  // 'none', 'zero', or 'first'
    },
    color: CATEGORY_COLORS.transform1d,
  },
  shift_diff: {
    type: 'shift_diff',
    label: 'Shift-Diff',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Shift-Diff',
      n: 1,
      diffMode: 'raw'  // 'raw', 'percent', 'log', 'cagr'
    },
    color: CATEGORY_COLORS.transform1d,
  },
  conv1d_custom: {
    type: 'conv1d_custom',
    label: 'Convolution 1D',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Conv1D',
      kernel: '0.25, 0.5, 0.25',  // User-defined kernel as comma-separated string
      padding: 'valid'  // 'valid' (no padding) or 'same' (preserve length)
    },
    color: CATEGORY_COLORS.transform1d,
  },
  sign: {
    type: 'sign',
    label: 'Sign',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Sign' },
    color: CATEGORY_COLORS.transform1d,
  },
  sin: {
    type: 'sin',
    label: 'Sin',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Sin' },
    color: CATEGORY_COLORS.transform1d,
  },
  cos: {
    type: 'cos',
    label: 'Cos',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Cos' },
    color: CATEGORY_COLORS.transform1d,
  },
  rsi: {
    type: 'rsi',
    label: 'RSI',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'RSI',
      period: 14
    },
    color: CATEGORY_COLORS.transform1d,
  },
  macd: {
    type: 'macd',
    label: 'MACD',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [
      { name: 'macd', type: 'tensor' },
      { name: 'signal', type: 'tensor' },
      { name: 'histogram', type: 'tensor' }
    ],
    defaultData: { 
      label: 'MACD',
      fastPeriod: 12,
      slowPeriod: 26,
      signalPeriod: 9
    },
    color: CATEGORY_COLORS.transform1d,
  },
  bollinger: {
    type: 'bollinger',
    label: 'Bollinger Bands',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [
      { name: 'upper', type: 'tensor' },
      { name: 'middle', type: 'tensor' },
      { name: 'lower', type: 'tensor' }
    ],
    defaultData: { 
      label: 'Bollinger',
      period: 20,
      stdDev: 2
    },
    color: CATEGORY_COLORS.transform1d,
  },

  // ========== Aggregation Operations ==========
  sum: {
    type: 'sum',
    label: 'Sum',
    category: 'aggregation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { 
      label: 'Sum',
    },
    color: CATEGORY_COLORS.aggregation,
  },
  mean: {
    type: 'mean',
    label: 'Mean',
    category: 'aggregation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { 
      label: 'Mean',
    },
    color: CATEGORY_COLORS.aggregation,
  },
  std: {
    type: 'std',
    label: 'Std Dev',
    category: 'aggregation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { 
      label: 'Std Dev',
      ddof: 0  // 0 = population, 1 = sample
    },
    color: CATEGORY_COLORS.aggregation,
  },
  variance: {
    type: 'variance',
    label: 'Variance',
    category: 'aggregation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { 
      label: 'Variance',
      ddof: 0  // 0 = population, 1 = sample
    },
    color: CATEGORY_COLORS.aggregation,
  },
  min: {
    type: 'min',
    label: 'Min',
    category: 'aggregation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { label: 'Min' },
    color: CATEGORY_COLORS.aggregation,
  },
  max: {
    type: 'max',
    label: 'Max',
    category: 'aggregation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { label: 'Max' },
    color: CATEGORY_COLORS.aggregation,
  },

  // ========== Multi-dimension Transformations ==========
  concat: {
    type: 'concat',
    label: 'Concat',
    category: 'transformNd',
    inputs: [
      { name: 'input_0', type: 'tensor' },
      { name: 'input_1', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Concat',
      numInputs: 2,  // User can increase this
      axis: 0        // 0 = stack into rows (N x L matrix)
    },
    color: CATEGORY_COLORS.transformNd,
  },
  transpose: {
    type: 'transpose',
    label: 'Transpose',
    category: 'transformNd',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Transpose' },
    color: CATEGORY_COLORS.transformNd,
  },
  matmul: {
    type: 'matmul',
    label: 'Matrix Multiply',
    category: 'transformNd',
    inputs: [
      { name: 'a', type: 'tensor' },
      { name: 'b', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'MatMul' },
    color: CATEGORY_COLORS.transformNd,
  },

  // ========== ML Layers ==========
  linear: {
    type: 'linear',
    label: 'Linear',
    category: 'ml',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Linear',
      name: 'linear',
      inFeatures: 10,
      outFeatures: 1
    },
    color: CATEGORY_COLORS.ml,
  },
  relu: {
    type: 'relu',
    label: 'ReLU',
    category: 'ml',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'ReLU' },
    color: CATEGORY_COLORS.ml,
  },
  tanh: {
    type: 'tanh',
    label: 'Tanh',
    category: 'ml',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Tanh' },
    color: CATEGORY_COLORS.ml,
  },
  sigmoid: {
    type: 'sigmoid',
    label: 'Sigmoid',
    category: 'ml',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Sigmoid' },
    color: CATEGORY_COLORS.ml,
  },
  softmax: {
    type: 'softmax',
    label: 'Softmax',
    category: 'ml',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Softmax' },
    color: CATEGORY_COLORS.ml,
  },
  lstm: {
    type: 'lstm',
    label: 'LSTM',
    category: 'ml',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [
      { name: 'output', type: 'tensor' },
      { name: 'hidden', type: 'tensor' }
    ],
    defaultData: { 
      label: 'LSTM',
      name: 'lstm',
      inputSize: 10,
      hiddenSize: 32,
      numLayers: 1
    },
    color: CATEGORY_COLORS.ml,
  },
  conv1d: {
    type: 'conv1d',
    label: 'Conv1D',
    category: 'ml',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Conv1D',
      name: 'conv1d',
      inChannels: 1,
      outChannels: 16,
      kernelSize: 3
    },
    color: CATEGORY_COLORS.ml,
  },

  // ========== Output ==========
  output: {
    type: 'output',
    label: 'Output',
    category: 'output',
    inputs: [{ name: 'input', type: 'scalar' }],
    outputs: [],
    defaultData: { 
      label: 'Position Delta',
      description: 'Output: positive = buy, negative = sell'
    },
    color: CATEGORY_COLORS.output,
  },
};

// Category order and labels for the toolbox
export const CATEGORY_ORDER = [
  { id: 'data', label: 'Data Sources' },
  { id: 'transform1d', label: '1-D Transformations' },
  { id: 'aggregation', label: 'Aggregation' },
  { id: 'transformNd', label: 'Multi-dim Transforms' },
  { id: 'ml', label: 'ML Layers' },
  { id: 'output', label: 'Output' },
];

// Get node types grouped by category (in order)
export function getNodeTypesByCategory(): Record<string, NodeTypeDefinition[]> {
  const categories: Record<string, NodeTypeDefinition[]> = {};
  
  CATEGORY_ORDER.forEach(cat => {
    categories[cat.id] = [];
  });
  
  Object.values(NODE_TYPES).forEach(def => {
    if (categories[def.category]) {
      categories[def.category].push(def);
    }
  });
  
  return categories;
}

// Get a specific node type definition
export function getNodeTypeDef(type: string): NodeTypeDefinition | undefined {
  return NODE_TYPES[type as VisualNodeType];
}
