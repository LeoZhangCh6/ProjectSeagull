/**
 * Node type definitions for the Visual Agent Designer.
 * Defines all available node types, their inputs/outputs, colors, and default data.
 */

import type { NodeTypeDefinition, VisualNodeType } from '../../types';

// Color palette for different node categories
export const CATEGORY_COLORS = {
  data: '#22c55e',      // Green - data sources
  operation: '#3b82f6', // Blue - math operations
  indicator: '#f59e0b', // Amber - technical indicators
  ml: '#8b5cf6',        // Purple - ML layers
  output: '#ef4444',    // Red - output
};

// All node type definitions
export const NODE_TYPES: Record<VisualNodeType, NodeTypeDefinition> = {
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
      initType: 'random' // 'random', 'zeros', 'ones'
    },
    color: CATEGORY_COLORS.data,
  },

  // ========== Basic Operations ==========
  slice: {
    type: 'slice',
    label: 'Slice',
    category: 'operation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Slice',
      n: 10
    },
    color: CATEGORY_COLORS.operation,
  },
  concat: {
    type: 'concat',
    label: 'Concat',
    category: 'operation',
    inputs: [
      { name: 'input1', type: 'tensor' },
      { name: 'input2', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Concat',
      axis: 0
    },
    color: CATEGORY_COLORS.operation,
  },
  add: {
    type: 'add',
    label: 'Add',
    category: 'operation',
    inputs: [
      { name: 'a', type: 'tensor' },
      { name: 'b', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Add (+)' },
    color: CATEGORY_COLORS.operation,
  },
  subtract: {
    type: 'subtract',
    label: 'Subtract',
    category: 'operation',
    inputs: [
      { name: 'a', type: 'tensor' },
      { name: 'b', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Subtract (-)' },
    color: CATEGORY_COLORS.operation,
  },
  multiply: {
    type: 'multiply',
    label: 'Multiply',
    category: 'operation',
    inputs: [
      { name: 'a', type: 'tensor' },
      { name: 'b', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Multiply (×)' },
    color: CATEGORY_COLORS.operation,
  },
  divide: {
    type: 'divide',
    label: 'Divide',
    category: 'operation',
    inputs: [
      { name: 'a', type: 'tensor' },
      { name: 'b', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Divide (÷)' },
    color: CATEGORY_COLORS.operation,
  },
  matmul: {
    type: 'matmul',
    label: 'Matrix Multiply',
    category: 'operation',
    inputs: [
      { name: 'a', type: 'tensor' },
      { name: 'b', type: 'tensor' }
    ],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'MatMul' },
    color: CATEGORY_COLORS.operation,
  },
  mean: {
    type: 'mean',
    label: 'Mean',
    category: 'operation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { 
      label: 'Mean',
      axis: null
    },
    color: CATEGORY_COLORS.operation,
  },
  sum: {
    type: 'sum',
    label: 'Sum',
    category: 'operation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { 
      label: 'Sum',
      axis: null
    },
    color: CATEGORY_COLORS.operation,
  },
  std: {
    type: 'std',
    label: 'Std Dev',
    category: 'operation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { 
      label: 'Std',
      axis: null
    },
    color: CATEGORY_COLORS.operation,
  },
  min: {
    type: 'min',
    label: 'Min',
    category: 'operation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { label: 'Min' },
    color: CATEGORY_COLORS.operation,
  },
  max: {
    type: 'max',
    label: 'Max',
    category: 'operation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'scalar' }],
    defaultData: { label: 'Max' },
    color: CATEGORY_COLORS.operation,
  },
  normalize: {
    type: 'normalize',
    label: 'Normalize',
    category: 'operation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { label: 'Normalize (z-score)' },
    color: CATEGORY_COLORS.operation,
  },
  clip: {
    type: 'clip',
    label: 'Clip',
    category: 'operation',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Clip',
      min: -1,
      max: 1
    },
    color: CATEGORY_COLORS.operation,
  },

  // ========== Technical Indicators ==========
  rolling_mean: {
    type: 'rolling_mean',
    label: 'Rolling Mean',
    category: 'indicator',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Rolling Mean',
      window: 10
    },
    color: CATEGORY_COLORS.indicator,
  },
  rolling_std: {
    type: 'rolling_std',
    label: 'Rolling Std',
    category: 'indicator',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'Rolling Std',
      window: 10
    },
    color: CATEGORY_COLORS.indicator,
  },
  rsi: {
    type: 'rsi',
    label: 'RSI',
    category: 'indicator',
    inputs: [{ name: 'input', type: 'tensor' }],
    outputs: [{ name: 'output', type: 'tensor' }],
    defaultData: { 
      label: 'RSI',
      period: 14
    },
    color: CATEGORY_COLORS.indicator,
  },
  macd: {
    type: 'macd',
    label: 'MACD',
    category: 'indicator',
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
    color: CATEGORY_COLORS.indicator,
  },
  bollinger: {
    type: 'bollinger',
    label: 'Bollinger Bands',
    category: 'indicator',
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
    color: CATEGORY_COLORS.indicator,
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

// Get node types grouped by category
export function getNodeTypesByCategory(): Record<string, NodeTypeDefinition[]> {
  const categories: Record<string, NodeTypeDefinition[]> = {
    data: [],
    operation: [],
    indicator: [],
    ml: [],
    output: [],
  };
  
  Object.values(NODE_TYPES).forEach(def => {
    categories[def.category].push(def);
  });
  
  return categories;
}

// Get a specific node type definition
export function getNodeTypeDef(type: string): NodeTypeDefinition | undefined {
  return NODE_TYPES[type as VisualNodeType];
}
