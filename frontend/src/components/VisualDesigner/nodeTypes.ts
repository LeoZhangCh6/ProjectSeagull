/**
 * Node type definitions for the Visual Agent Designer.
 * Defines all available node types, their inputs/outputs, colors, and default data.
 */

import type { NodeTypeDefinition, VisualNodeType } from '../../types';

// Color palette for different node categories
export const CATEGORY_COLORS = {
  data: '#22c55e',        // Green - data sources
  scalar: '#ec4899',      // Pink - scalar-to-scalar operations
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
  timestamp: {
    type: 'timestamp',
    label: 'Timestamp',
    category: 'data',
    inputs: [],
    outputs: [
      { name: 'year', type: 'scalar' },
      { name: 'month', type: 'scalar' },
      { name: 'weeknumber', type: 'scalar' },
      { name: 'day_of_week', type: 'scalar' },
      { name: 'hour', type: 'scalar' },
      { name: 'timestamp_seconds', type: 'scalar' },
    ],
    defaultData: { label: 'Timestamp' },
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
    inputs: [{ name: 'new_value', type: 'any' }],
    outputs: [{ name: 'value', type: 'any' }],
    defaultData: { 
      label: 'Custom State',
      stateName: 'my_state',
      defaultValue: '0',
      shape: [1],
    },
    color: CATEGORY_COLORS.data,
  },
  custom_state_t: {
    type: 'custom_state_t',
    label: '',  // Set to {name}_t when created
    category: 'data',
    inputs: [],
    outputs: [{ name: 'value', type: 'any' }],
    defaultData: { 
      label: 'my_state_t',
      stateName: 'my_state',
      defaultValue: '0',
      shape: [1],
      statePairId: '',
    },
    color: CATEGORY_COLORS.data,  // Green
  },
  custom_state_t1: {
    type: 'custom_state_t1',
    label: '',  // Set to {name}_(t+1) when created
    category: 'data',
    inputs: [{ name: 'new_value', type: 'any' }],
    outputs: [],
    defaultData: { 
      label: 'my_state_(t+1)',
      stateName: 'my_state',
      defaultValue: '0',
      shape: [1],
      statePairId: '',
    },
    color: CATEGORY_COLORS.output,  // Red
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
    defaultData: { 
      label: 'Subtract (-)',
      subtractMode: 'difference'  // 'difference' (a-b) or 'ratio' ((a-b)/b)
    },
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
  round: {
    type: 'round',
    label: 'Round',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Round',
      decimals: 0,
      roundMethod: 'nearest',  // 'nearest', 'up', 'down'
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
      diffMode: 'raw'  // 'raw', 'ratio', 'log', 'cagr' (ratio = (x-x_lag)/x_lag, no *100)
    },
    color: CATEGORY_COLORS.transform1d,
  },
  conv1d_custom: {
    type: 'conv1d_custom',
    label: 'Convolution 1D',
    category: 'transform1d',
    inputs: [
      { name: 'input', type: 'tensor' },
      { name: 'kernel', type: 'tensor' },  // 1D vector as convolution kernel
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Conv1D',
      padding: 'valid'  // 'valid' (no padding) or 'same' (preserve length)
    },
    color: CATEGORY_COLORS.transform1d,
  },
  abs: {
    type: 'abs',
    label: 'Abs',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Abs' },
    color: CATEGORY_COLORS.transform1d,
  },
  parity_check: {
    type: 'parity_check',
    label: 'Parity Check',
    category: 'scalar',
    inputs: [
      { name: 'a', type: 'scalar' },
      { name: 'b', type: 'scalar' }
    ],
    outputs: [
      { name: 'parity', type: 'scalar' },       // 1 same sign, -1 opposite, 0 any zero
      { name: 'aligned_sign', type: 'scalar' }  // 1 both pos, -1 both neg, 0 otherwise
    ],
    defaultData: { label: 'Parity Check' },
    color: CATEGORY_COLORS.scalar,
  },
  flip: {
    type: 'flip',
    label: 'Flip',
    category: 'scalar',
    inputs: [{ name: 'input', type: 'scalar' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { label: 'Flip', flipMode: 'parity' },  // 'parity' (-1↔1, 0→0) or 'boolean' (0↔1)
    color: CATEGORY_COLORS.scalar,
  },
  parity_split: {
    type: 'parity_split',
    label: 'Parity Split',
    category: 'scalar',
    inputs: [{ name: 'input', type: 'scalar' }],
    outputs: [
      { name: 'positive', type: 'scalar' },  // value if input > 0, else 0
      { name: 'negative', type: 'scalar' },  // value if input < 0, else 0
    ],
    defaultData: { label: 'Parity Split' },
    color: CATEGORY_COLORS.scalar,
  },
  compare: {
    type: 'compare',
    label: 'Compare',
    category: 'scalar',
    inputs: [
      { name: 'a', type: 'scalar' },
      { name: 'b', type: 'scalar' }
    ],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { 
      label: 'Compare',
      compareOp: 'gt',  // 'gt', 'lt', 'gte', 'lte', 'eq', 'neq'
    },
    color: CATEGORY_COLORS.scalar,
  },
  crossover: {
    type: 'crossover',
    label: 'Crossover',
    category: 'scalar',
    inputs: [
      { name: 'fast', type: 'scalar' },
      { name: 'slow', type: 'scalar' }
    ],
    outputs: [
      { name: 'cross_above', type: 'scalar' },  // 1 if fast just crossed above slow, else 0
      { name: 'cross_below', type: 'scalar' },  // 1 if fast just crossed below slow, else 0
    ],
    defaultData: { label: 'Crossover' },
    color: CATEGORY_COLORS.scalar,
  },
  threshold: {
    type: 'threshold',
    label: 'Threshold',
    category: 'scalar',
    inputs: [{ name: 'input', type: 'scalar' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { 
      label: 'Threshold',
      threshold: 0,
      mode: 'above',  // 'above' (1 if input > threshold), 'below' (1 if input < threshold)
    },
    color: CATEGORY_COLORS.scalar,
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
  ema: {
    type: 'ema',
    label: 'EMA',
    category: 'transform1d',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'EMA',
      span: 10,  // EMA span (like pandas ewm span)
    },
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
  view_output: {
    type: 'view_output',
    label: 'View Output',
    category: 'output',
    inputs: [{ name: 'input', type: 'any' }],
    outputs: [],
    defaultData: { 
      label: 'View Output',
      description: 'Meter/debugger: shows sparkline, scalar, or 2D heatmap'
    },
    color: CATEGORY_COLORS.output,
  },
};

// Category order and labels for the toolbox
export const CATEGORY_ORDER = [
  { id: 'data', label: 'Data Sources' },
  { id: 'scalar', label: 'Scalar Ops' },
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
