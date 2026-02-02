/**
 * Visual Agent Designer - Main Component
 * 
 * A node-based visual programming environment for designing trading agents.
 * Uses ReactFlow for the canvas and node connections.
 */

import { useCallback, useState, useRef, useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  Node,
  Edge,
  Connection,
  NodeChange,
  EdgeChange,
  ReactFlowProvider,
  useReactFlow,
  EdgeProps,
  getBezierPath,
  BaseEdge,
  EdgeLabelRenderer,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { X, Save, Play, Code, FolderOpen, Plus, Trash2, Upload, Download, XCircle } from 'lucide-react';
import { nodeTypes } from './CustomNodes';
import { getNodeTypesByCategory, NODE_TYPES, CATEGORY_COLORS, CATEGORY_ORDER } from './nodeTypes';
import { visualDesignerApi, signalsApi } from '../../api/client';
import type { Signal, VisualDesign, VisualDesignGraph, CodeGenerationResult, ValidationResult } from '../../types';

// ============================================================================
// Shape Tracking System
// ============================================================================

// Shape type: [rows, cols] where cols can be number or 'L' (unknown length)
type ShapeDim = number | 'L';
type Shape = [ShapeDim, ShapeDim];

// Check if two shapes are compatible for element-wise operations
function shapesCompatibleElementWise(a: Shape | null, b: Shape | null): boolean {
  if (!a || !b) return true; // Allow if shape unknown
  const [aRows, aCols] = a;
  const [bRows, bCols] = b;
  
  // Rows must match or one must be 1 (broadcasting)
  const rowsOk = aRows === bRows || aRows === 1 || bRows === 1 || aRows === 'L' || bRows === 'L';
  // Cols must match or one must be 1 (broadcasting)
  const colsOk = aCols === bCols || aCols === 1 || bCols === 1 || aCols === 'L' || bCols === 'L';
  
  return rowsOk && colsOk;
}

// Check if shapes are compatible for matrix multiplication: (R1, C1) x (C1, R2) -> (R1, R2)
function shapesCompatibleMatMul(a: Shape | null, b: Shape | null): boolean {
  if (!a || !b) return true;
  const [, aCols] = a;
  const [bRows,] = b;
  
  // Inner dimensions must match
  if (aCols === 'L' || bRows === 'L') return true;
  return aCols === bRows;
}

// Format shape for display
function formatShape(shape: Shape | null): string {
  if (!shape) return '(?, ?)';
  const [rows, cols] = shape;
  return `(${rows}, ${cols})`;
}

// Compute output shape for a node based on its type and input shapes
function computeNodeShape(
  nodeType: string,
  data: Record<string, any>,
  inputShapes: Record<string, Shape | null>
): Shape | null {
  const getInputShape = (key: string): Shape | null => inputShapes[key] || null;
  
  // Scalar category nodes: always output [1, 1] regardless of input
  const nodeTypeDef = NODE_TYPES[nodeType];
  if (nodeTypeDef?.category === 'scalar') {
    return [1, 1];
  }
  
  switch (nodeType) {
    // Data Sources - all output (1, L) or (1, N)
    case 'signal':
      return [1, 'L'];
    
    case 'constant': {
      const shape = data.shape || [1];
      if (shape.length === 1) {
        return shape[0] === 1 ? [1, 1] : [1, shape[0]];
      }
      return [shape[0], shape[1] || 1];
    }
    
    case 'variable': {
      const shape = data.shape || [1];
      if (shape.length === 1) {
        return shape[0] === 1 ? [1, 1] : [1, shape[0]];
      }
      return [shape[0], shape[1] || 1];
    }
    
    case 'range': {
      const n = getDataNumber(data, 'n', 10);
      return [1, n];
    }
    
    // Timestamp - outputs 6 scalars (year, month, weeknumber, day_of_week, hour, timestamp_seconds)
    case 'timestamp':
      return [1, 1];
    
    // Agent State - outputs 3 scalars
    case 'agent_state':
      return [1, 1]; // Each output is a scalar
    
    // Agent Equity Curve - outputs historical equity signal
    case 'agent_equity_curve': {
      const historyLength = getDataNumber(data, 'historyLength', 50);
      return [1, historyLength];
    }
    
    // Custom State - shape depends on user setting
    case 'custom_state':
    case 'custom_state_t':
    case 'custom_state_t1': {
      const shape = data.shape || [1];
      if (shape.length === 1) {
        return shape[0] === 1 ? [1, 1] : [1, shape[0]];
      }
      return [shape[0], shape[1] || 1];
    }

    // Slice - outputs (1, N-M)
    case 'slice': {
      const n = getDataNumber(data, 'n', 10);
      const m = getDataNumber(data, 'm', 0);
      return [1, n - m];
    }
    
    // Shift - depends on fill mode
    case 'shift': {
      const inputShape = getInputShape('input');
      const n = getDataNumber(data, 'n', 1);
      const fillMode = data.fillMode || 'none';
      
      if (!inputShape) return [1, 'L'];
      const [rows, cols] = inputShape;
      
      if (fillMode === 'none') {
        // Shorter output
        if (cols === 'L') return [rows, 'L'];
        return [rows, Math.max(0, cols - n)];
      }
      return inputShape;
    }
    
    // Shift-Diff - always shorter
    case 'shift_diff': {
      const inputShape = getInputShape('input');
      const n = getDataNumber(data, 'n', 1);
      
      if (!inputShape) return [1, 'L'];
      const [rows, cols] = inputShape;
      
      if (cols === 'L') return [rows, 'L'];
      return [rows, Math.max(0, cols - n)];
    }
    
    // Conv1D Custom - output depends on padding mode; kernel from input
    case 'conv1d_custom': {
      const inputShape = getInputShape('input');
      const kernelShape = getInputShape('kernel');
      const padding = data.padding || 'valid';
      
      if (!inputShape) return [1, 'L'];
      const [rows, cols] = inputShape;
      
      if (padding === 'same') {
        return inputShape; // Same length as input
      }
      // 'valid' padding - output length = input length - kernel_size + 1
      const kernelSize = kernelShape && kernelShape[1] !== 'L' ? (kernelShape[1] as number) : 1;
      if (cols === 'L') return [rows, 'L'];
      return [rows, Math.max(0, (cols as number) - kernelSize + 1)];
    }
    
    // Element-wise operations - shape matches inputs
    case 'add':
    case 'subtract':
    case 'multiply':
    case 'divide': {
      const shapeA = getInputShape('a');
      const shapeB = getInputShape('b');
      
      if (!shapeA && !shapeB) return null;
      if (!shapeA) return shapeB;
      if (!shapeB) return shapeA;
      
      // Result shape is max of both (broadcasting)
      const [aRows, aCols] = shapeA;
      const [bRows, bCols] = shapeB;
      
      const rows = aRows === 'L' ? bRows : bRows === 'L' ? aRows : Math.max(aRows as number, bRows as number);
      const cols = aCols === 'L' ? bCols : bCols === 'L' ? aCols : Math.max(aCols as number, bCols as number);
      
      return [rows, cols];
    }
    
    // Normalize, Clip, Round, etc. - same shape as input
    case 'normalize':
    case 'clip':
    case 'round':
    case 'rolling_mean':
    case 'rolling_std':
    case 'ema':
    case 'rsi':
    case 'relu':
    case 'tanh':
    case 'sigmoid':
    case 'softmax':
    case 'sign':
    case 'sin':
    case 'cos':
    case 'abs': {
      const inputShape = getInputShape('input');
      return inputShape || [1, 'L'];
    }
    
    // MACD, Bollinger - same as input (for primary output)
    case 'macd':
    case 'bollinger': {
      const inputShape = getInputShape('input');
      return inputShape || [1, 'L'];
    }
    
    // Aggregation - always outputs (1, 1)
    case 'sum':
    case 'mean':
    case 'std':
    case 'variance':
    case 'min':
    case 'max':
      return [1, 1];
    
    // Concat - stacks inputs into (N, L) matrix
    case 'concat': {
      const numInputs = data.numInputs || 2;
      let maxCols: ShapeDim = 0;
      
      for (let i = 0; i < numInputs; i++) {
        const inputShape = getInputShape(`input_${i}`);
        if (inputShape) {
          const [, cols] = inputShape;
          if (cols === 'L') {
            maxCols = 'L';
          } else if (maxCols !== 'L') {
            maxCols = Math.max(maxCols as number, cols as number);
          }
        }
      }
      
      return [numInputs, maxCols === 0 ? 'L' : maxCols];
    }
    
    // Transpose - swap dimensions
    case 'transpose': {
      const inputShape = getInputShape('input');
      if (!inputShape) return ['L', 1];
      return [inputShape[1], inputShape[0]];
    }
    
    // MatMul - (R1, C1) x (C1, R2) -> (R1, R2)
    case 'matmul': {
      const shapeA = getInputShape('a');
      const shapeB = getInputShape('b');
      
      if (!shapeA || !shapeB) return [1, 1];
      
      const [aRows,] = shapeA;
      const [, bCols] = shapeB;
      
      return [aRows, bCols];
    }
    
    // Linear layer
    case 'linear': {
      const inputShape = getInputShape('input');
      const outFeatures = data.outFeatures || 1;
      
      if (!inputShape) return [1, outFeatures];
      return [inputShape[0], outFeatures];
    }
    
    // LSTM
    case 'lstm': {
      const inputShape = getInputShape('input');
      const hiddenSize = data.hiddenSize || 32;
      
      if (!inputShape) return [1, hiddenSize];
      return [inputShape[0], hiddenSize];
    }
    
    // Conv1D
    case 'conv1d': {
      const inputShape = getInputShape('input');
      const outChannels = data.outChannels || 16;
      
      if (!inputShape) return [outChannels, 'L'];
      const [, cols] = inputShape;
      return [outChannels, cols];
    }
    
    // Output - scalar (1, 1)
    case 'output':
      return [1, 1];
    
    // View Output - pass-through (meter/debugger)
    case 'view_output': {
      return getInputShape('input');
    }
    
    default:
      return null;
  }
}

// ============================================================================
// Preview Computation Engine
// ============================================================================

// Node output types: 'tensor' (1D array) or 'scalar' (single number)
type PreviewData = { type: 'tensor'; values: number[] } | { type: 'scalar'; value: number } | { type: 'scalars'; values: number[] } | { type: 'matrix'; values: number[][] };

// ISO week number of year (1–53)
function getWeekNumber(d: Date): number {
  const start = new Date(d.getFullYear(), 0, 1);
  const diff = d.getTime() - start.getTime();
  return Math.ceil((diff / 86400000 + start.getDay() + 1) / 7);
}

// Parse numeric value from node data (may be string from text input to allow empty and negative typing)
function getDataNumber(data: Record<string, any>, key: string, fallback: number): number {
  const v = data[key];
  if (typeof v === 'number' && !isNaN(v)) return v;
  const n = parseFloat(v);
  return isNaN(n) ? fallback : n;
}

// Generate base signal data for a signal node
function generateSignalPreviewData(signalId: string, cachedData?: number[]): PreviewData {
  if (cachedData && cachedData.length > 0) {
    return { type: 'tensor', values: cachedData };
  }
  // Fallback: generate deterministic demo data
  const seed = signalId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const basePrice = 100 + (seed % 500);
  const values = Array.from({ length: 20 }, (_, i) => {
    const t = i / 20;
    return basePrice + 
      Math.sin(t * 4 + seed * 0.1) * basePrice * 0.05 +
      Math.cos(t * 7) * basePrice * 0.02 +
      (seed % 2 === 0 ? t * basePrice * 0.03 : -t * basePrice * 0.02);
  });
  return { type: 'tensor', values };
}

// Compute preview for a node based on its type and input previews
function computeNodePreview(
  nodeType: string,
  data: Record<string, any>,
  inputs: Record<string, PreviewData>,
  signalCache: Record<string, number[]>
): PreviewData {
  // Helper to get tensor values from input
  const getTensorValues = (key: string): number[] => {
    const input = inputs[key];
    if (!input) return [];
    if (input.type === 'tensor') return input.values;
    if (input.type === 'scalars') return input.values;  // Multi-scalar as array
    return Array(20).fill(input.value); // Expand scalar to tensor
  };
  
  const getScalarValue = (key: string): number => {
    const input = inputs[key];
    if (!input) return 0;
    if (input.type === 'scalar') return input.value;
    if (input.type === 'scalars') return input.values[0] || 0;  // Use first scalar
    // Reduce tensor to scalar (use last value)
    return input.values.length > 0 ? input.values[input.values.length - 1] : 0;
  };

  // For binary ops: treat scalar, scalars[1], and tensor[1] as scalar (shows number not sparkline)
  const getScalarLike = (input: PreviewData | undefined) => {
    if (!input) return { isScalar: false, value: null as number | null };
    if (input.type === 'scalar') return { isScalar: true, value: input.value };
    if (input.type === 'scalars' && input.values.length === 1) return { isScalar: true, value: input.values[0] };
    if (input.type === 'tensor' && input.values.length === 1) return { isScalar: true, value: input.values[0] };
    return { isScalar: false, value: null };
  };

  switch (nodeType) {
    // Data sources
    case 'signal': {
      const signalId = data.signalId || 'unknown';
      return generateSignalPreviewData(signalId, signalCache[signalId]);
    }
    
    case 'constant': {
      const value = getDataNumber(data, 'value', 0);
      const shape = data.shape || [1];
      if (shape.length === 1 && shape[0] === 1) {
        return { type: 'scalar', value };
      }
      return { type: 'tensor', values: Array(Math.min(shape[0], 20)).fill(value) };
    }
    
    case 'variable': {
      const shape = data.shape || [1];
      const initType = data.initType || 'zeros';
      
      // If shape has more than 1 dimension, no preview
      if (shape.length > 1) {
        return { type: 'tensor', values: [] };
      }
      
      const size = Math.min(shape[0], 20);
      
      // Generate values based on initialization type
      let values: number[];
      if (initType === 'zeros') {
        values = Array(size).fill(0);
      } else if (initType === 'ones') {
        values = Array(size).fill(1);
      } else {
        // random
        values = Array(size).fill(0).map(() => Math.random() * 0.02 - 0.01);
      }
      
      if (size === 1) {
        return { type: 'scalar', value: values[0] };
      }
      return { type: 'tensor', values };
    }
    
    // Range node - linear range
    case 'range': {
      const n = getDataNumber(data, 'n', 10);
      const start = getDataNumber(data, 'start', 0);
      const mode = data.mode || 'step';
      
      let values: number[];
      if (mode === 'step') {
        const step = getDataNumber(data, 'step', 1);
        values = Array.from({ length: n }, (_, i) => start + i * step);
      } else {
        // 'end' mode
        const end = getDataNumber(data, 'end', 10);
        const step = n > 1 ? (end - start) / (n - 1) : 0;
        values = Array.from({ length: n }, (_, i) => start + i * step);
      }
      return { type: 'tensor', values: values.slice(0, 20) };
    }
    
    // Agent State - returns demo values (shares, equity, cash)
    // Timestamp - demo values from current date
    case 'timestamp': {
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth() + 1;
      const weekNum = getWeekNumber(now);
      const dayOfWeek = now.getDay(); // 0=Sun, 1=Mon, ...
      const hour = now.getHours();
      const tsSec = Math.floor(now.getTime() / 1000);
      return { type: 'scalars', values: [year, month, weekNum, dayOfWeek, hour, tsSec] };
    }
    
    // Agent State - returns 3 scalars (shares, equity, cash), each dot outputs one
    case 'agent_state': {
      const shares = data.demoShares ?? 10;
      const equity = data.demoEquity ?? 100000;
      // For demo: assume stock price ~$100, so cash = equity - shares * 100
      const stockPrice = 100;
      const cash = equity - shares * stockPrice;
      return { type: 'scalars', values: [shares, equity, cash] };
    }
    
    // Agent Equity Curve - simulated historical equity with noise
    case 'agent_equity_curve': {
      const historyLength = data.historyLength || 50;
      const equity = data.demoEquity ?? 100000;
      // Generate demo equity curve with random walk
      const values: number[] = [];
      let current = equity * 0.95; // Start slightly below current
      for (let i = 0; i < historyLength; i++) {
        values.push(current);
        // Random walk with slight upward drift
        current += current * (Math.random() - 0.48) * 0.02;
      }
      // End at current equity
      values[historyLength - 1] = equity;
      return { type: 'tensor', values: values.slice(0, 20) };
    }
    
    // Custom State - returns default value
    case 'custom_state':
    case 'custom_state_t': {
      const defaultValue = data.defaultValue || '0';
      const values = defaultValue.split(',').map((s: string) => parseFloat(s.trim()) || 0);
      if (values.length === 1) {
        return { type: 'scalar', value: values[0] };
      }
      return { type: 'tensor', values: values.slice(0, 20) };
    }
    case 'custom_state_t1':
      return { type: 'scalar', value: 0 };
    
    // Slice - outputs tensor, window from -N to -M (M=0 means end)
    case 'slice': {
      const inputVals = getTensorValues('input');
      const n = getDataNumber(data, 'n', 10);
      const m = getDataNumber(data, 'm', 0);
      
      if (inputVals.length === 0) return { type: 'tensor', values: [] };
      
      // slice(-n, -m) or slice(-n) if m=0
      const startIdx = Math.max(0, inputVals.length - n);
      const endIdx = m === 0 ? inputVals.length : Math.max(0, inputVals.length - m);
      
      return { type: 'tensor', values: inputVals.slice(startIdx, endIdx) };
    }
    
    // Concat - outputs tensor or matrix (2D when stacking rows)
    case 'concat': {
      const numInputs = data.numInputs || 2;
      const allInputs: number[][] = [];
      const maxCols = 20;
      for (let i = 0; i < numInputs; i++) {
        const inputKey = `input_${i}`;
        const inputVals = getTensorValues(inputKey);
        if (inputVals.length > 0) {
          allInputs.push(inputVals.slice(0, maxCols));
        }
      }
      if (allInputs.length === 0) return { type: 'tensor', values: [] };
      if (allInputs.length === 1) return { type: 'tensor', values: allInputs[0] };
      // 2+ rows -> matrix for heatmap in View Output
      return { type: 'matrix', values: allInputs };
    }
    
    // Binary operations - output matches input shape
    case 'add': {
      const { isScalar: isScalarA, value: scalarAValue } = getScalarLike(inputs['a']);
      const { isScalar: isScalarB, value: scalarBValue } = getScalarLike(inputs['b']);
      
      // Both scalars -> scalar result
      if (isScalarA && isScalarB && scalarAValue !== null && scalarBValue !== null) {
        return { type: 'scalar', value: scalarAValue + scalarBValue };
      }
      
      // At least one tensor -> tensor result
      const a = getTensorValues('a');
      const b = getTensorValues('b');
      if (a.length === 0 && b.length === 0) return { type: 'scalar', value: 0 };
      const maxLen = Math.max(a.length, b.length);
      const aExpanded = a.length === 1 ? Array(maxLen).fill(a[0]) : a;
      const bExpanded = b.length === 1 ? Array(maxLen).fill(b[0]) : b;
      const values = aExpanded.map((v, i) => v + (bExpanded[i] ?? 0));
      if (values.length === 1) {
        return { type: 'scalar', value: values[0] };
      }
      return { type: 'tensor', values };
    }
    
    case 'subtract': {
      const { isScalar: isScalarA, value: scalarAValue } = getScalarLike(inputs['a']);
      const { isScalar: isScalarB, value: scalarBValue } = getScalarLike(inputs['b']);
      const subtractMode = data.subtractMode || 'difference';

      if (subtractMode === 'ratio') {
        if (isScalarA && isScalarB && scalarAValue !== null && scalarBValue !== null) {
          return { type: 'scalar', value: scalarBValue !== 0 ? (scalarAValue - scalarBValue) / scalarBValue : 0 };
        }
        const a = getTensorValues('a');
        const b = getTensorValues('b');
        if (a.length === 0 && b.length === 0) return { type: 'scalar', value: 0 };
        const maxLen = Math.max(a.length, b.length);
        const aExpanded = a.length === 1 ? Array(maxLen).fill(a[0]) : a;
        const bExpanded = b.length === 1 ? Array(maxLen).fill(b[0]) : b;
        const values = aExpanded.map((v, i) => {
          const den = bExpanded[i] ?? 0;
          return den !== 0 ? (v - den) / den : 0;
        });
        if (values.length === 1) {
          return { type: 'scalar', value: values[0] };
        }
        return { type: 'tensor', values };
      }

      // Difference: a - b
      if (isScalarA && isScalarB && scalarAValue !== null && scalarBValue !== null) {
        return { type: 'scalar', value: scalarAValue - scalarBValue };
      }
      const a = getTensorValues('a');
      const b = getTensorValues('b');
      if (a.length === 0 && b.length === 0) return { type: 'scalar', value: 0 };
      const maxLen = Math.max(a.length, b.length);
      const aExpanded = a.length === 1 ? Array(maxLen).fill(a[0]) : a;
      const bExpanded = b.length === 1 ? Array(maxLen).fill(b[0]) : b;
      const values = aExpanded.map((v, i) => v - (bExpanded[i] ?? 0));
      if (values.length === 1) {
        return { type: 'scalar', value: values[0] };
      }
      return { type: 'tensor', values };
    }
    
    case 'multiply': {
      const { isScalar: isScalarA, value: scalarAValue } = getScalarLike(inputs['a']);
      const { isScalar: isScalarB, value: scalarBValue } = getScalarLike(inputs['b']);
      
      // Both scalars -> scalar result
      if (isScalarA && isScalarB && scalarAValue !== null && scalarBValue !== null) {
        return { type: 'scalar', value: scalarAValue * scalarBValue };
      }
      
      // At least one tensor -> tensor result
      const a = getTensorValues('a');
      const b = getTensorValues('b');
      if (a.length === 0 && b.length === 0) return { type: 'scalar', value: 0 };
      const maxLen = Math.max(a.length, b.length);
      const aExpanded = a.length === 1 ? Array(maxLen).fill(a[0]) : a;
      const bExpanded = b.length === 1 ? Array(maxLen).fill(b[0]) : b;
      const values = aExpanded.map((v, i) => v * (bExpanded[i] ?? 1));
      if (values.length === 1) {
        return { type: 'scalar', value: values[0] };
      }
      return { type: 'tensor', values };
    }
    
    case 'divide': {
      const { isScalar: isScalarA, value: scalarAValue } = getScalarLike(inputs['a']);
      const { isScalar: isScalarB, value: scalarBValue } = getScalarLike(inputs['b']);
      
      // Both scalars -> scalar result
      if (isScalarA && isScalarB && scalarAValue !== null && scalarBValue !== null) {
        const divisor = scalarBValue || 1;
        return { type: 'scalar', value: scalarAValue / divisor };
      }
      
      // At least one tensor -> tensor result
      const a = getTensorValues('a');
      const b = getTensorValues('b');
      if (a.length === 0 && b.length === 0) return { type: 'scalar', value: 0 };
      const maxLen = Math.max(a.length, b.length);
      const aExpanded = a.length === 1 ? Array(maxLen).fill(a[0]) : a;
      const bExpanded = b.length === 1 ? Array(maxLen).fill(b[0]) : b;
      const values = aExpanded.map((v, i) => v / (bExpanded[i] || 1));
      if (values.length === 1) {
        return { type: 'scalar', value: values[0] };
      }
      return { type: 'tensor', values };
    }
    
    // Transpose - swap rows and columns (for preview, just return input)
    case 'transpose': {
      const input = getTensorValues('input');
      return { type: 'tensor', values: input };
    }
    
    case 'matmul': {
      // MatMul typically reduces dimension - return scalar for simplicity
      const a = getTensorValues('a');
      const b = getTensorValues('b');
      const dot = a.reduce((sum, v, i) => sum + v * (b[i] ?? 0), 0);
      return { type: 'scalar', value: dot };
    }
    
    // Aggregation operations - output scalar
    case 'mean': {
      const input = getTensorValues('input');
      if (input.length === 0) return { type: 'scalar', value: 0 };
      return { type: 'scalar', value: input.reduce((a, b) => a + b, 0) / input.length };
    }
    
    case 'sum': {
      const input = getTensorValues('input');
      return { type: 'scalar', value: input.reduce((a, b) => a + b, 0) };
    }
    
    case 'std': {
      const input = getTensorValues('input');
      if (input.length === 0) return { type: 'scalar', value: 0 };
      const ddof = data.ddof ?? 0; // 0 = population, 1 = sample
      const n = input.length;
      const mean = input.reduce((a, b) => a + b, 0) / n;
      const variance = input.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(n - ddof, 1);
      return { type: 'scalar', value: Math.sqrt(variance) };
    }
    
    case 'variance': {
      const input = getTensorValues('input');
      if (input.length === 0) return { type: 'scalar', value: 0 };
      const ddof = data.ddof ?? 0; // 0 = population, 1 = sample
      const n = input.length;
      const mean = input.reduce((a, b) => a + b, 0) / n;
      const variance = input.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(n - ddof, 1);
      return { type: 'scalar', value: variance };
    }
    
    case 'min': {
      const input = getTensorValues('input');
      return { type: 'scalar', value: input.length > 0 ? Math.min(...input) : 0 };
    }
    
    case 'max': {
      const input = getTensorValues('input');
      return { type: 'scalar', value: input.length > 0 ? Math.max(...input) : 0 };
    }
    
    // Transform operations - output tensor
    case 'normalize': {
      const input = getTensorValues('input');
      if (input.length === 0) return { type: 'tensor', values: [] };
      const mean = input.reduce((a, b) => a + b, 0) / input.length;
      const std = Math.sqrt(input.reduce((a, b) => a + (b - mean) ** 2, 0) / input.length) || 1;
      return { type: 'tensor', values: input.map(v => (v - mean) / std) };
    }
    
    case 'clip': {
      const input = getTensorValues('input');
      const minVal = getDataNumber(data, 'min', -1);
      const maxVal = getDataNumber(data, 'max', 1);
      return { type: 'tensor', values: input.map(v => Math.max(minVal, Math.min(maxVal, v))) };
    }
    
    // Round - nearest, up, or down
    case 'round': {
      const input = getTensorValues('input');
      const decimals = getDataNumber(data, 'decimals', 0);
      const method = data.roundMethod || 'nearest';
      const factor = Math.pow(10, decimals);
      const values = input.map(v => {
        const scaled = v * factor;
        let rounded: number;
        if (method === 'up') rounded = Math.ceil(scaled);
        else if (method === 'down') rounded = Math.floor(scaled);
        else rounded = Math.round(scaled);
        return rounded / factor;
      });
      return { type: 'tensor', values };
    }
    
    // Abs - absolute value
    case 'abs': {
      const input = getTensorValues('input');
      return { type: 'tensor', values: input.map(v => Math.abs(v)) };
    }
    // Parity Check: SCALAR CATEGORY - always coerce inputs to scalars
    case 'parity_check': {
      const aVal = getScalarValue('a');
      const bVal = getScalarValue('b');
      
      const parity = (x: number, y: number) => {
        if (x === 0 || y === 0) return 0;
        return (x > 0 && y > 0) || (x < 0 && y < 0) ? 1 : -1;
      };
      const alignedSign = (x: number, y: number) => {
        if (x === 0 || y === 0) return 0;
        if ((x > 0 && y > 0) || (x < 0 && y < 0)) return x > 0 ? 1 : -1;
        return 0;
      };
      
      const p = parity(aVal, bVal);
      const a = alignedSign(aVal, bVal);
      return { type: 'scalars', values: [p, a] };
    }
    // Flip: parity (-1↔1, 0→0) or boolean (0↔1)
    case 'flip': {
      const v = getScalarValue('input');
      const flipMode = data.flipMode || 'parity';
      let out: number;
      if (flipMode === 'boolean') {
        out = v === 0 ? 1 : 0;  // 0↔1
      } else {
        if (v === 0) out = 0;
        else if (v === 1 || v === -1) out = -v;  // -1↔1
        else out = v > 0 ? -1 : 1;  // other positive → -1, other negative → 1
      }
      return { type: 'scalar', value: out };
    }
    // Parity Split: positive→first output, negative→second output
    case 'parity_split': {
      const v = getScalarValue('input');
      const pos = v > 0 ? v : 0;
      const neg = v < 0 ? v : 0;
      return { type: 'scalars', values: [pos, neg] };
    }
    // Compare: a op b → 1 or 0
    case 'compare': {
      const a = getScalarValue('a');
      const b = getScalarValue('b');
      const op = data.compareOp || 'gt';
      let result: number;
      switch (op) {
        case 'gt': result = a > b ? 1 : 0; break;
        case 'lt': result = a < b ? 1 : 0; break;
        case 'gte': result = a >= b ? 1 : 0; break;
        case 'lte': result = a <= b ? 1 : 0; break;
        case 'eq': result = a === b ? 1 : 0; break;
        case 'neq': result = a !== b ? 1 : 0; break;
        default: result = 0;
      }
      return { type: 'scalar', value: result };
    }
    // Crossover: detects when fast crosses slow (uses prev values - demo shows 0)
    case 'crossover': {
      // In preview we don't have state, so just show 0
      return { type: 'scalars', values: [0, 0] };
    }
    // Threshold: input > threshold → 1 or 0
    case 'threshold': {
      const v = getScalarValue('input');
      const t = getDataNumber(data, 'threshold', 0);
      const mode = data.mode || 'above';
      const result = mode === 'below' ? (v < t ? 1 : 0) : (v > t ? 1 : 0);
      return { type: 'scalar', value: result };
    }
    // Sign function: 1 if > 0, 0 if = 0, -1 if < 0
    case 'sign': {
      const input = getTensorValues('input');
      return { type: 'tensor', values: input.map(v => v > 0 ? 1 : (v < 0 ? -1 : 0)) };
    }
    // Sin function
    case 'sin': {
      const input = getTensorValues('input');
      return { type: 'tensor', values: input.map(v => Math.sin(v)) };
    }
    
    // Cos function
    case 'cos': {
      const input = getTensorValues('input');
      return { type: 'tensor', values: input.map(v => Math.cos(v)) };
    }
    
    // Rolling operations - output tensor
    case 'rolling_mean': {
      const input = getTensorValues('input');
      const window = getDataNumber(data, 'window', 10);
      const values = input.map((_, i, arr) => {
        const start = Math.max(0, i - window + 1);
        const slice = arr.slice(start, i + 1);
        return slice.reduce((a, b) => a + b, 0) / slice.length;
      });
      return { type: 'tensor', values };
    }
    
    case 'rolling_std': {
      const input = getTensorValues('input');
      const window = getDataNumber(data, 'window', 10);
      const values = input.map((_, i, arr) => {
        const start = Math.max(0, i - window + 1);
        const slice = arr.slice(start, i + 1);
        const m = slice.reduce((a, b) => a + b, 0) / slice.length;
        return Math.sqrt(slice.reduce((a, b) => a + (b - m) ** 2, 0) / slice.length);
      });
      return { type: 'tensor', values };
    }
    
    // EMA - exponential moving average
    case 'ema': {
      const input = getTensorValues('input');
      const span = getDataNumber(data, 'span', 10);
      if (input.length === 0) return { type: 'tensor', values: [] };
      const alpha = 2 / (span + 1);
      const values: number[] = [input[0]];
      for (let i = 1; i < input.length; i++) {
        values.push(alpha * input[i] + (1 - alpha) * values[i - 1]);
      }
      return { type: 'tensor', values };
    }
    
    // Shift - shift back n positions
    case 'shift': {
      const input = getTensorValues('input');
      const n = getDataNumber(data, 'n', 1);
      const fillMode = data.fillMode || 'none';
      
      if (input.length === 0) return { type: 'tensor', values: [] };
      
      if (fillMode === 'none') {
        // No padding - output is shorter by n elements
        if (input.length <= n) return { type: 'tensor', values: [] };
        return { type: 'tensor', values: input.slice(0, input.length - n) };
      }
      
      // Shift back by n: output[i] = input[i-n] for i >= n
      const values: number[] = [];
      for (let i = 0; i < input.length; i++) {
        if (i < n) {
          // Fill the first n positions
          values.push(fillMode === 'first' ? input[0] : 0);
        } else {
          values.push(input[i - n]);
        }
      }
      return { type: 'tensor', values };
    }
    
    // Shift-Diff - difference between x(i) and x(i-n), no padding (shorter output)
    case 'shift_diff': {
      const input = getTensorValues('input');
      const n = getDataNumber(data, 'n', 1);
      const diffMode = data.diffMode || 'raw';
      
      if (input.length <= n) return { type: 'tensor', values: [] };
      
      const values: number[] = [];
      // Start from index n (no padding, output length = input length - n)
      for (let i = n; i < input.length; i++) {
        const current = input[i];
        const previous = input[i - n];
        
        switch (diffMode) {
          case 'raw':
            values.push(current - previous);
            break;
          case 'percent':
          case 'ratio':
            // (x(i) - x(i-n)) / x(i-n), no * 100
            values.push(previous !== 0 ? (current - previous) / previous : 0);
            break;
          case 'log':
            // log(x(i)) - log(x(i-n))
            values.push(current > 0 && previous > 0 ? Math.log(current) - Math.log(previous) : 0);
            break;
          case 'cagr':
            // (x(i)/x(i-n))^(1/n) - 1
            values.push(previous > 0 ? Math.pow(current / previous, 1 / n) - 1 : 0);
            break;
          default:
            values.push(current - previous);
        }
      }
      return { type: 'tensor', values };
    }
    
    // 1D Convolution with kernel from input (vector)
    case 'conv1d_custom': {
      const input = getTensorValues('input');
      const kernel = getTensorValues('kernel');
      const padding = data.padding || 'valid';
      
      if (kernel.length === 0 || input.length < kernel.length) {
        return { type: 'tensor', values: [] };
      }
      
      const values: number[] = [];
      
      if (padding === 'same') {
        const padSize = Math.floor(kernel.length / 2);
        for (let i = 0; i < input.length; i++) {
          let sum = 0;
          for (let k = 0; k < kernel.length; k++) {
            const inputIdx = i - padSize + k;
            const inputVal = inputIdx >= 0 && inputIdx < input.length ? input[inputIdx] : 0;
            sum += inputVal * kernel[k];
          }
          values.push(sum);
        }
      } else {
        for (let i = 0; i <= input.length - kernel.length; i++) {
          let sum = 0;
          for (let k = 0; k < kernel.length; k++) {
            sum += input[i + k] * kernel[k];
          }
          values.push(sum);
        }
      }
      
      return { type: 'tensor', values };
    }
    
    // RSI indicator - outputs tensor [0-100]
    case 'rsi': {
      const input = getTensorValues('input');
      const period = getDataNumber(data, 'period', 14);
      if (input.length < 2) return { type: 'tensor', values: [] };
      
      // Calculate price changes
      const changes = input.slice(1).map((v, i) => v - input[i]);
      const gains = changes.map(c => c > 0 ? c : 0);
      const losses = changes.map(c => c < 0 ? -c : 0);
      
      // Calculate RSI using SMA (simplified)
      const values = changes.map((_, i) => {
        const start = Math.max(0, i - period + 1);
        const avgGain = gains.slice(start, i + 1).reduce((a, b) => a + b, 0) / period;
        const avgLoss = losses.slice(start, i + 1).reduce((a, b) => a + b, 0) / period;
        if (avgLoss === 0) return 100;
        const rs = avgGain / avgLoss;
        return 100 - (100 / (1 + rs));
      });
      return { type: 'tensor', values: [50, ...values] }; // Pad to match length
    }
    
    // MACD indicator - outputs tensor (just MACD line for simplicity)
    case 'macd': {
      const input = getTensorValues('input');
      const fastPeriod = data.fastPeriod || 12;
      const slowPeriod = data.slowPeriod || 26;
      
      // Simplified EMA calculation
      const ema = (arr: number[], period: number): number[] => {
        const k = 2 / (period + 1);
        const result: number[] = [arr[0]];
        for (let i = 1; i < arr.length; i++) {
          result.push(arr[i] * k + result[i - 1] * (1 - k));
        }
        return result;
      };
      
      const fastEma = ema(input, fastPeriod);
      const slowEma = ema(input, slowPeriod);
      const macdLine = fastEma.map((v, i) => v - slowEma[i]);
      return { type: 'tensor', values: macdLine };
    }
    
    // Bollinger Bands - outputs tensor (middle band for simplicity)
    case 'bollinger': {
      const input = getTensorValues('input');
      const period = getDataNumber(data, 'period', 20);
      
      // Calculate middle band (SMA)
      const values = input.map((_, i, arr) => {
        const start = Math.max(0, i - period + 1);
        const slice = arr.slice(start, i + 1);
        return slice.reduce((a, b) => a + b, 0) / slice.length;
      });
      return { type: 'tensor', values };
    }
    
    // ML layers - output tensor (simplified)
    case 'linear': {
      const input = getTensorValues('input');
      // Simulate a linear transform with random weights
      const scale = 0.5;
      const bias = 0.1;
      return { type: 'tensor', values: input.map(v => v * scale + bias) };
    }
    
    case 'relu': {
      const input = getTensorValues('input');
      return { type: 'tensor', values: input.map(v => Math.max(0, v)) };
    }
    
    case 'tanh': {
      const input = getTensorValues('input');
      return { type: 'tensor', values: input.map(v => Math.tanh(v)) };
    }
    
    case 'sigmoid': {
      const input = getTensorValues('input');
      return { type: 'tensor', values: input.map(v => 1 / (1 + Math.exp(-v))) };
    }
    
    case 'softmax': {
      const input = getTensorValues('input');
      if (input.length === 0) return { type: 'tensor', values: [] };
      const maxVal = Math.max(...input);
      const exps = input.map(v => Math.exp(v - maxVal));
      const sum = exps.reduce((a, b) => a + b, 0);
      return { type: 'tensor', values: exps.map(v => v / sum) };
    }
    
    // LSTM - simplified, output hidden state representation
    case 'lstm': {
      const input = getTensorValues('input');
      // Simulate LSTM with tanh transformation
      return { type: 'tensor', values: input.map(v => Math.tanh(v * 0.1)) };
    }
    
    // Conv1D - simplified convolution
    case 'conv1d': {
      const input = getTensorValues('input');
      const kernelSize = data.kernelSize || 3;
      // Apply simple averaging kernel
      const values = input.map((_, i, arr) => {
        const start = Math.max(0, i - Math.floor(kernelSize / 2));
        const end = Math.min(arr.length, i + Math.floor(kernelSize / 2) + 1);
        const slice = arr.slice(start, end);
        return slice.reduce((a, b) => a + b, 0) / slice.length;
      });
      return { type: 'tensor', values };
    }
    
    // Output - always scalar
    case 'output': {
      return { type: 'scalar', value: getScalarValue('input') };
    }
    
    // View Output - pass-through (meter/debugger: sparkline, scalar, or heatmap)
    case 'view_output': {
      const input = inputs['input'];
      if (!input) return { type: 'tensor', values: [] };
      return input;
    }
    
    default:
      return { type: 'tensor', values: [] };
  }
}

// Topologically sort nodes and compute all previews
// Result type for computation
interface ComputeResult {
  previews: Record<string, PreviewData>;
  shapes: Record<string, Shape | null>;
}

function computeAllPreviews(
  nodes: Node[],
  edges: Edge[],
  signalCache: Record<string, number[]>
): ComputeResult {
  const previews: Record<string, PreviewData> = {};
  const shapes: Record<string, Shape | null> = {};
  const nodeMap = new Map(nodes.map(n => [n.id, n]));
  
  // Build adjacency and in-degree
  const inDegree = new Map<string, number>();
  const adjacency = new Map<string, string[]>();
  // nodeId -> (targetHandle -> { sourceId, sourceHandle })
  const incomingEdges = new Map<string, Map<string, { sourceId: string; sourceHandle?: string }>>();
  
  nodes.forEach(n => {
    inDegree.set(n.id, 0);
    adjacency.set(n.id, []);
    incomingEdges.set(n.id, new Map());
  });
  
  edges.forEach(edge => {
    if (nodeMap.has(edge.source) && nodeMap.has(edge.target)) {
      adjacency.get(edge.source)!.push(edge.target);
      inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
      incomingEdges.get(edge.target)!.set(edge.targetHandle || 'input', {
        sourceId: edge.source,
        sourceHandle: edge.sourceHandle || undefined,
      });
    }
  });
  
  // Topological sort using Kahn's algorithm
  const queue = nodes.filter(n => inDegree.get(n.id) === 0).map(n => n.id);
  const sortedIds: string[] = [];
  
  while (queue.length > 0) {
    const nodeId = queue.shift()!;
    sortedIds.push(nodeId);
    
    for (const neighbor of adjacency.get(nodeId) || []) {
      const newDegree = (inDegree.get(neighbor) || 1) - 1;
      inDegree.set(neighbor, newDegree);
      if (newDegree === 0) {
        queue.push(neighbor);
      }
    }
  }
  
  // Compute previews and shapes in topological order
  for (const nodeId of sortedIds) {
    const node = nodeMap.get(nodeId);
    if (!node) continue;
    
    const nodeType = node.type || 'unknown';
    const data = node.data || {};
    
    // Gather input previews and shapes
    const inputPreviews: Record<string, PreviewData> = {};
    const inputShapes: Record<string, Shape | null> = {};
    const incoming = incomingEdges.get(nodeId);
    if (incoming) {
      incoming.forEach(({ sourceId, sourceHandle }, targetHandle) => {
        let srcPreview = previews[sourceId];
        if (srcPreview) {
          // For multi-output nodes: extract the specific output when sourceHandle is set
          const sourceNode = nodeMap.get(sourceId);
          const sourceType = sourceNode?.type || 'unknown';
          const sourceDef = NODE_TYPES[sourceType as keyof typeof NODE_TYPES];
          if (sourceDef?.outputs?.length > 1 && sourceHandle) {
            const outIndex = sourceDef.outputs.findIndex((o: { name: string }) => o.name === sourceHandle);
            if (outIndex >= 0 && srcPreview.type === 'scalars' && srcPreview.values[outIndex] !== undefined) {
              srcPreview = { type: 'scalar', value: srcPreview.values[outIndex] };
            }
          }
          inputPreviews[targetHandle] = srcPreview;
        }
        inputShapes[targetHandle] = shapes[sourceId] || null;
      });
    }
    
    // Compute this node's preview and shape
    previews[nodeId] = computeNodePreview(nodeType, data, inputPreviews, signalCache);
    shapes[nodeId] = computeNodeShape(nodeType, data, inputShapes);
  }
  
  return { previews, shapes };
}

// Custom edge with delete button on hover
function DeletableEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  selected,
}: EdgeProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      {/* Invisible wider path for easier hovering */}
      <path
        d={edgePath}
        fill="none"
        strokeWidth={20}
        stroke="transparent"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={{ cursor: 'pointer' }}
      />
      <BaseEdge 
        path={edgePath} 
        markerEnd={markerEnd} 
        style={{
          ...style,
          stroke: selected ? '#fff' : isHovered ? '#ef4444' : '#64748b',
          strokeWidth: selected || isHovered ? 3 : 2,
        }}
      />
      {/* Delete button shown on hover or selection */}
      {(isHovered || selected) && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="nodrag nopan"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
          >
            <button
              className="w-5 h-5 bg-red-500 hover:bg-red-400 rounded-full flex items-center justify-center shadow-lg"
              onClick={(e) => {
                e.stopPropagation();
                // Dispatch custom event to delete edge
                window.dispatchEvent(new CustomEvent('delete-edge', { detail: { id } }));
              }}
              title="Delete connection"
            >
              <X className="w-3 h-3 text-white" />
            </button>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

// Edge types for ReactFlow
const edgeTypes = {
  deletable: DeletableEdge,
};

interface VisualDesignerProps {
  isOpen: boolean;
  onClose: () => void;
  initialDesign?: VisualDesign;
  onSave?: (design: VisualDesign) => void;
}

// Toolbox panel component
function Toolbox({ onAddNode }: { onAddNode: (type: string) => void }) {
  const categories = getNodeTypesByCategory();
  
  return (
    <div className="w-52 bg-[var(--bg-secondary)] border-r border-[var(--border-color)] overflow-y-auto">
      <div className="p-2 text-sm font-medium border-b border-[var(--border-color)]">
        Node Toolbox
      </div>
      {CATEGORY_ORDER.map(({ id: category, label: categoryLabel }) => {
        const nodes = categories[category] || [];
        if (nodes.length === 0) return null;
        
        return (
          <div key={category} className="border-b border-[var(--border-color)]">
            <div 
              className="px-2 py-1 text-xs font-medium text-[var(--text-secondary)]"
              style={{ borderLeft: `3px solid ${CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS]}` }}
            >
              {categoryLabel}
            </div>
            <div className="p-1 space-y-1">
              {nodes
                .filter(n => n.type !== 'custom_state_t' && n.type !== 'custom_state_t1')
                .map(node => (
                <button
                  key={node.type}
                  onClick={() => onAddNode(node.type)}
                  className="w-full px-2 py-1 text-left text-sm rounded hover:bg-[var(--bg-tertiary)] transition-colors"
                  style={{ borderLeft: `2px solid ${node.color}` }}
                >
                  {node.label}
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Properties panel for editing selected node
function PropertiesPanel({ 
  selectedNode, 
  onUpdateNode,
  signals 
}: { 
  selectedNode: Node | null;
  onUpdateNode: (id: string, data: any) => void;
  signals: Signal[];
}) {
  if (!selectedNode) {
    return (
      <div className="w-64 bg-[var(--bg-secondary)] border-l border-[var(--border-color)] p-4">
        <div className="text-sm text-[var(--text-secondary)]">
          Select a node to edit its properties
        </div>
      </div>
    );
  }
  
  const nodeType = selectedNode.type || 'unknown';
  const data = selectedNode.data || {};
  
  const handleChange = (key: string, value: any) => {
    onUpdateNode(selectedNode.id, { ...data, [key]: value });
  };
  
  // Display value for numeric inputs (allows empty and '-' while typing)
  const numVal = (key: string, fallback: string = '') => {
    const v = data[key];
    return v !== undefined && v !== null ? String(v) : fallback;
  };
  
  return (
    <div className="w-64 bg-[var(--bg-secondary)] border-l border-[var(--border-color)] overflow-y-auto">
      <div className="p-3 border-b border-[var(--border-color)]">
        <div className="text-sm font-medium">Node Properties</div>
        <div className="text-xs text-[var(--text-secondary)]">{nodeType}</div>
      </div>
      
      <div className="p-3 space-y-3">
        {/* Label */}
        <div>
          <label className="block text-xs text-[var(--text-secondary)] mb-1">Label</label>
          <input
            type="text"
            value={data.label || ''}
            onChange={(e) => handleChange('label', e.target.value)}
            className="w-full text-sm"
          />
        </div>
        
        {/* Sparkline Type - show for nodes that output tensors */}
        {!['output', 'agent_state', 'timestamp'].includes(nodeType) && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Sparkline Type</label>
            <select
              value={data.sparklineType || 'line'}
              onChange={(e) => handleChange('sparklineType', e.target.value)}
              className="w-full text-sm"
            >
              <option value="line">Line Chart</option>
              <option value="bar">Bar Chart</option>
            </select>
          </div>
        )}
        
        {/* Signal-specific: signal selector and frequency */}
        {nodeType === 'signal' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Signal</label>
              <select
                value={data.signalId || ''}
                onChange={(e) => {
                  const newSignalId = e.target.value;
                  const signal = signals.find(s => s.id === newSignalId);
                  // Update both signalId and frequency in a single call to avoid stale data issues
                  const updates: Record<string, any> = { signalId: newSignalId };
                  if (signal?.model_freq) {
                    updates.frequency = signal.model_freq;
                  }
                  onUpdateNode(selectedNode.id, { ...data, ...updates });
                }}
                className="w-full text-sm"
              >
                <option value="">Select signal...</option>
                {signals.map(s => (
                  <option key={s.id} value={s.id}>{s.id} ({s.model_freq || 'unknown'})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Frequency</label>
              <select
                value={data.frequency || '1D'}
                onChange={(e) => handleChange('frequency', e.target.value)}
                className="w-full text-sm"
              >
                <option value="1T">1 Minute</option>
                <option value="5T">5 Minutes</option>
                <option value="15T">15 Minutes</option>
                <option value="1H">1 Hour</option>
                <option value="1D">1 Day</option>
                <option value="1W">1 Week</option>
              </select>
            </div>
          </>
        )}
        
        {/* Constant-specific */}
        {nodeType === 'constant' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Value</label>
              <input
                type="text"
                inputMode="decimal"
                value={numVal('value', '')}
                onChange={(e) => handleChange('value', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Shape (comma-separated)</label>
              <input
                type="text"
                value={(data.shape || [1]).join(',')}
                onChange={(e) => handleChange('shape', e.target.value.split(',').map(s => parseInt(s.trim()) || 1))}
                className="w-full text-sm"
              />
            </div>
          </>
        )}
        
        {/* Variable-specific */}
        {nodeType === 'variable' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Name</label>
              <input
                type="text"
                value={data.name || 'weight'}
                onChange={(e) => handleChange('name', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Shape (comma-separated)</label>
              <input
                type="text"
                value={(data.shape || [1]).join(',')}
                onChange={(e) => handleChange('shape', e.target.value.split(',').map(s => parseInt(s.trim()) || 1))}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Initialization</label>
              <select
                value={data.initType || 'random'}
                onChange={(e) => handleChange('initType', e.target.value)}
                className="w-full text-sm"
              >
                <option value="random">Random</option>
                <option value="zeros">Zeros</option>
                <option value="ones">Ones</option>
              </select>
            </div>
          </>
        )}
        
        {/* Range-specific */}
        {nodeType === 'range' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">N (number of elements)</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('n', '10')}
                onChange={(e) => handleChange('n', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Start</label>
              <input
                type="text"
                inputMode="decimal"
                value={numVal('start', '')}
                onChange={(e) => handleChange('start', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Mode</label>
              <select
                value={data.mode || 'step'}
                onChange={(e) => handleChange('mode', e.target.value)}
                className="w-full text-sm"
              >
                <option value="step">N, Start, Step</option>
                <option value="end">N, Start, End</option>
              </select>
            </div>
            {data.mode === 'end' ? (
              <div>
                <label className="block text-xs text-[var(--text-secondary)] mb-1">End</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={numVal('end', '10')}
                  onChange={(e) => handleChange('end', e.target.value)}
                  className="w-full text-sm"
                />
              </div>
            ) : (
              <div>
                <label className="block text-xs text-[var(--text-secondary)] mb-1">Step</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={numVal('step', '1')}
                  onChange={(e) => handleChange('step', e.target.value)}
                  className="w-full text-sm"
                />
              </div>
            )}
          </>
        )}
        
        {/* Agent State */}
        {nodeType === 'agent_state' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Demo Shares Held</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('demoShares', '10')}
                onChange={(e) => handleChange('demoShares', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Demo Total Equity</label>
              <input
                type="text"
                inputMode="decimal"
                value={numVal('demoEquity', '100000')}
                onChange={(e) => handleChange('demoEquity', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div className="text-[10px] text-[var(--text-secondary)] mt-2">
              Outputs: shares, equity, cash (equity - shares × price)
            </div>
          </>
        )}
        
        {/* Agent Equity Curve */}
        {nodeType === 'agent_equity_curve' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">History Length</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('historyLength', '50')}
                onChange={(e) => handleChange('historyLength', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Demo Equity</label>
              <input
                type="text"
                inputMode="decimal"
                value={numVal('demoEquity', '100000')}
                onChange={(e) => handleChange('demoEquity', e.target.value)}
                className="w-full text-sm"
              />
            </div>
          </>
        )}
        
        {/* Custom State (legacy single block) */}
        {nodeType === 'custom_state' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">State Name</label>
              <input
                type="text"
                value={data.stateName || 'my_state'}
                onChange={(e) => handleChange('stateName', e.target.value)}
                className="w-full text-sm font-mono"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Default Value</label>
              <input
                type="text"
                value={data.defaultValue || '0'}
                onChange={(e) => handleChange('defaultValue', e.target.value)}
                className="w-full text-sm font-mono"
                placeholder="0 or 1,2,3 for vector"
              />
            </div>
            <div className="text-[10px] text-[var(--text-secondary)] mt-2">
              Connect "new_value" input to update state each step.
              Output returns current state value.
            </div>
          </>
        )}
        {/* Custom State _t and _(t+1) pair */}
        {(nodeType === 'custom_state_t' || nodeType === 'custom_state_t1') && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">State Name (synced with pair)</label>
              <input
                type="text"
                value={data.stateName || 'my_state'}
                onChange={(e) => handleChange('stateName', e.target.value)}
                className="w-full text-sm font-mono"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Default Value</label>
              <input
                type="text"
                value={data.defaultValue || '0'}
                onChange={(e) => handleChange('defaultValue', e.target.value)}
                className="w-full text-sm font-mono"
                placeholder="0 or 1,2,3 for vector"
              />
            </div>
            <div className="text-[10px] text-[var(--text-secondary)] mt-2">
              {nodeType === 'custom_state_t' ? 'Green: reads current state (input).' : 'Red: connect value here to update state for next step (output).'}
              Rename or delete one and the pair updates together.
            </div>
          </>
        )}
        {/* Subtract mode */}
        {nodeType === 'subtract' && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Mode</label>
            <select
              value={data.subtractMode || 'difference'}
              onChange={(e) => handleChange('subtractMode', e.target.value)}
              className="w-full text-sm"
            >
              <option value="difference">Difference: a - b</option>
              <option value="ratio">Ratio: (a - b) / b</option>
            </select>
          </div>
        )}
        
        {/* Flip-specific */}
        {nodeType === 'flip' && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Flip Mode</label>
            <select
              value={data.flipMode || 'parity'}
              onChange={(e) => handleChange('flipMode', e.target.value)}
              className="w-full text-sm"
            >
              <option value="parity">Parity: -1↔1, 0→0</option>
              <option value="boolean">Boolean: 0↔1</option>
            </select>
          </div>
        )}
        
        {/* Compare-specific */}
        {nodeType === 'compare' && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Comparison Operator</label>
            <select
              value={data.compareOp || 'gt'}
              onChange={(e) => handleChange('compareOp', e.target.value)}
              className="w-full text-sm"
            >
              <option value="gt">a {'>'} b (greater than)</option>
              <option value="lt">a {'<'} b (less than)</option>
              <option value="gte">a ≥ b (greater or equal)</option>
              <option value="lte">a ≤ b (less or equal)</option>
              <option value="eq">a = b (equal)</option>
              <option value="neq">a ≠ b (not equal)</option>
            </select>
          </div>
        )}
        
        {/* Threshold-specific */}
        {nodeType === 'threshold' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Threshold Value</label>
              <input
                type="text"
                inputMode="decimal"
                value={numVal('threshold', '0')}
                onChange={(e) => handleChange('threshold', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Mode</label>
              <select
                value={data.mode || 'above'}
                onChange={(e) => handleChange('mode', e.target.value)}
                className="w-full text-sm"
              >
                <option value="above">Above: input {'>'} threshold → 1</option>
                <option value="below">Below: input {'<'} threshold → 1</option>
              </select>
            </div>
          </>
        )}
        
        {/* EMA-specific */}
        {nodeType === 'ema' && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Span (periods)</label>
            <input
              type="text"
              inputMode="numeric"
              value={numVal('span', '10')}
              onChange={(e) => handleChange('span', e.target.value)}
              className="w-full text-sm"
            />
          </div>
        )}
        
        {/* Slice-specific */}
        {nodeType === 'slice' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">From last N (start)</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('n', '10')}
                onChange={(e) => handleChange('n', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">To last M (end, 0=end)</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('m', '0')}
                onChange={(e) => handleChange('m', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div className="text-xs text-[var(--text-secondary)] mt-1">
              Window: [-{getDataNumber(data, 'n', 10)} : {getDataNumber(data, 'm', 0) === 0 ? 'end' : `-${getDataNumber(data, 'm', 0)}`}]
            </div>
          </>
        )}
        
        {/* Clip-specific */}
        {nodeType === 'clip' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Min</label>
              <input
                type="text"
                inputMode="decimal"
                value={numVal('min', '-1')}
                onChange={(e) => handleChange('min', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Max</label>
              <input
                type="text"
                inputMode="decimal"
                value={numVal('max', '1')}
                onChange={(e) => handleChange('max', e.target.value)}
                className="w-full text-sm"
              />
            </div>
          </>
        )}
        
        {/* Round-specific */}
        {nodeType === 'round' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Decimals</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('decimals', '0')}
                onChange={(e) => handleChange('decimals', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Round Method</label>
              <select
                value={data.roundMethod || 'nearest'}
                onChange={(e) => handleChange('roundMethod', e.target.value)}
                className="w-full text-sm"
              >
                <option value="nearest">Round to nearest (default)</option>
                <option value="up">Round up (ceil)</option>
                <option value="down">Round down (floor)</option>
              </select>
            </div>
          </>
        )}
        
        {/* Rolling ops */}
        {(nodeType === 'rolling_mean' || nodeType === 'rolling_std') && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Window</label>
            <input
              type="text"
              inputMode="numeric"
              value={numVal('window', '10')}
              onChange={(e) => handleChange('window', e.target.value)}
              className="w-full text-sm"
            />
          </div>
        )}
        
        {/* Shift */}
        {nodeType === 'shift' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Shift (n positions)</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('n', '1')}
                onChange={(e) => handleChange('n', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Fill Mode</label>
              <select
                value={data.fillMode || 'none'}
                onChange={(e) => handleChange('fillMode', e.target.value)}
                className="w-full text-sm"
              >
                <option value="none">No padding (shorter output)</option>
                <option value="zero">Fill with 0</option>
                <option value="first">Fill with first value</option>
              </select>
            </div>
          </>
        )}
        
        {/* Shift-Diff */}
        {nodeType === 'shift_diff' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Lag (n periods)</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('n', '1')}
                onChange={(e) => handleChange('n', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Difference Mode</label>
              <select
                value={data.diffMode || 'raw'}
                onChange={(e) => handleChange('diffMode', e.target.value)}
                className="w-full text-sm"
              >
                <option value="raw">Raw: x(i) - x(i-n)</option>
                <option value="ratio">Ratio: (x(i)-x(i-n))/x(i-n)</option>
                <option value="log">Log: log(x(i)) - log(x(i-n))</option>
                <option value="cagr">CAGR: (x(i)/x(i-n))^(1/n) - 1</option>
              </select>
            </div>
          </>
        )}
        
        {/* Conv1D Custom */}
        {nodeType === 'conv1d_custom' && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Padding Mode</label>
            <select
              value={data.padding || 'valid'}
              onChange={(e) => handleChange('padding', e.target.value)}
              className="w-full text-sm"
            >
              <option value="valid">Valid (no padding, shorter output)</option>
              <option value="same">Same (preserve length)</option>
            </select>
            <div className="text-[10px] text-[var(--text-secondary)] mt-1">
              Connect a 1D vector to the <strong>kernel</strong> input for the convolution kernel.
            </div>
          </div>
        )}
        
        {/* RSI */}
        {nodeType === 'rsi' && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Period</label>
            <input
              type="text"
              inputMode="numeric"
              value={numVal('period', '14')}
              onChange={(e) => handleChange('period', e.target.value)}
              className="w-full text-sm"
            />
          </div>
        )}
        
        {/* MACD */}
        {nodeType === 'macd' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Fast Period</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('fastPeriod', '12')}
                onChange={(e) => handleChange('fastPeriod', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Slow Period</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('slowPeriod', '26')}
                onChange={(e) => handleChange('slowPeriod', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Signal Period</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('signalPeriod', '9')}
                onChange={(e) => handleChange('signalPeriod', e.target.value)}
                className="w-full text-sm"
              />
            </div>
          </>
        )}
        
        {/* Bollinger Bands */}
        {nodeType === 'bollinger' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Period</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('period', '20')}
                onChange={(e) => handleChange('period', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Std Dev Multiplier</label>
              <input
                type="text"
                inputMode="decimal"
                value={numVal('stdDev', '2')}
                onChange={(e) => handleChange('stdDev', e.target.value)}
                className="w-full text-sm"
              />
            </div>
          </>
        )}
        
        {/* Std Dev and Variance - ddof option */}
        {(nodeType === 'std' || nodeType === 'variance') && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Type</label>
            <select
              value={data.ddof ?? 0}
              onChange={(e) => handleChange('ddof', parseInt(e.target.value))}
              className="w-full text-sm"
            >
              <option value={0}>Population (ddof=0)</option>
              <option value={1}>Sample (ddof=1)</option>
            </select>
          </div>
        )}
        
        {/* Concat - number of inputs */}
        {nodeType === 'concat' && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Number of Inputs</label>
            <input
              type="text"
              inputMode="numeric"
              value={numVal('numInputs', '2')}
              onChange={(e) => handleChange('numInputs', e.target.value)}
              className="w-full text-sm"
            />
            <div className="text-xs text-[var(--text-secondary)] mt-1">
              Creates {getDataNumber(data, 'numInputs', 2)} input ports (input_0, input_1, ...)
            </div>
          </div>
        )}
        
        {/* Linear layer */}
        {nodeType === 'linear' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Input Features</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('inFeatures', '10')}
                onChange={(e) => handleChange('inFeatures', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Output Features</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('outFeatures', '1')}
                onChange={(e) => handleChange('outFeatures', e.target.value)}
                className="w-full text-sm"
              />
            </div>
          </>
        )}
        
        {/* LSTM */}
        {nodeType === 'lstm' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Input Size</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('inputSize', '10')}
                onChange={(e) => handleChange('inputSize', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Hidden Size</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('hiddenSize', '32')}
                onChange={(e) => handleChange('hiddenSize', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Num Layers</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('numLayers', '1')}
                onChange={(e) => handleChange('numLayers', e.target.value)}
                className="w-full text-sm"
              />
            </div>
          </>
        )}
        
        {/* Conv1D */}
        {nodeType === 'conv1d' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">In Channels</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('inChannels', '1')}
                onChange={(e) => handleChange('inChannels', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Out Channels</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('outChannels', '16')}
                onChange={(e) => handleChange('outChannels', e.target.value)}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Kernel Size</label>
              <input
                type="text"
                inputMode="numeric"
                value={numVal('kernelSize', '3')}
                onChange={(e) => handleChange('kernelSize', e.target.value)}
                className="w-full text-sm"
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Code preview panel
function CodePanel({ 
  code, 
  errors, 
  warnings,
  onClose 
}: { 
  code: string;
  errors: string[];
  warnings: string[];
  onClose: () => void;
}) {
  return (
    <div className="absolute inset-4 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg shadow-2xl z-50 flex flex-col">
      <div className="flex items-center justify-between p-3 border-b border-[var(--border-color)]">
        <div className="font-medium">Generated Python Code</div>
        <button onClick={onClose} className="p-1 hover:bg-[var(--bg-tertiary)] rounded">
          <X className="w-5 h-5" />
        </button>
      </div>
      
      {errors.length > 0 && (
        <div className="p-3 bg-red-900/50 border-b border-red-700">
          <div className="text-red-400 font-medium mb-1">Errors:</div>
          <ul className="text-sm text-red-300 list-disc list-inside">
            {errors.map((e, i) => <li key={i}>{e}</li>)}
          </ul>
        </div>
      )}
      
      {warnings.length > 0 && (
        <div className="p-3 bg-yellow-900/50 border-b border-yellow-700">
          <div className="text-yellow-400 font-medium mb-1">Warnings:</div>
          <ul className="text-sm text-yellow-300 list-disc list-inside">
            {warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}
      
      <div className="flex-1 overflow-auto p-4">
        <pre className="text-sm font-mono text-gray-300 whitespace-pre-wrap">{code || '# No code generated'}</pre>
      </div>
    </div>
  );
}

// Main canvas component (needs to be inside ReactFlowProvider)
function DesignerCanvas({ 
  initialDesign,
  onSave,
  onClose 
}: { 
  initialDesign?: VisualDesign;
  onSave?: (design: VisualDesign) => void;
  onClose: () => void;
}) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();
  
  // State
  const [nodes, setNodes] = useState<Node[]>(initialDesign?.graph_json?.nodes || []);
  const [edges, setEdges] = useState<Edge[]>(initialDesign?.graph_json?.edges || []);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdges, setSelectedEdges] = useState<string[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [designName, setDesignName] = useState(initialDesign?.name || 'Untitled Design');
  const [symbol, setSymbol] = useState(initialDesign?.symbol || 'AAPL');
  const [timespan, setTimespan] = useState(initialDesign?.primary_timespan || 'day');
  const [multiplier, setMultiplier] = useState(initialDesign?.primary_multiplier || 1);
  const [designId, setDesignId] = useState<number | null>(initialDesign?.id || null);
  
  // Code panel state
  const [showCode, setShowCode] = useState(false);
  const [generatedCode, setGeneratedCode] = useState<CodeGenerationResult | null>(null);
  
  // Validation state
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  
  // Signal data cache for previews
  const [signalCache, setSignalCache] = useState<Record<string, number[]>>({});
  
  // Load signals on mount
  useEffect(() => {
    signalsApi.list()
      .then(data => {
        console.log('[VisualDesigner] Loaded signals:', data);
        setSignals(data);
      })
      .catch(err => {
        console.error('[VisualDesigner] Failed to load signals:', err);
      });
  }, []);
  
  // Fetch signal preview data when signal nodes are added or changed
  useEffect(() => {
    const signalNodes = nodes.filter(n => n.type === 'signal');
    const signalIds = signalNodes.map(n => n.data?.signalId).filter(Boolean) as string[];
    
    // Fetch data for any signals not in cache
    signalIds.forEach(signalId => {
      if (!signalCache[signalId]) {
        visualDesignerApi.getSignalPreview(signalId, 20)
          .then(preview => {
            if (preview?.values?.length > 0) {
              setSignalCache(prev => ({ ...prev, [signalId]: preview.values }));
            }
          })
          .catch(err => {
            console.warn(`Failed to fetch signal preview for ${signalId}:`, err);
          });
      }
    });
  }, [nodes]);
  
  // Compute all node previews based on graph topology
  // Compute previews and shapes
  const { previews: nodePreviews, shapes: nodeShapes } = useMemo(() => {
    return computeAllPreviews(nodes, edges, signalCache);
  }, [nodes, edges, signalCache]);
  
  // Create nodes with preview and shape data injected
  const nodesWithPreviews = useMemo(() => {
    return nodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        _preview: nodePreviews[node.id],
        _shape: nodeShapes[node.id],
      },
    }));
  }, [nodes, nodePreviews, nodeShapes]);
  
  // Handle edge deletion from custom event
  useEffect(() => {
    const handleDeleteEdge = (e: CustomEvent<{ id: string }>) => {
      setEdges((eds) => eds.filter((edge) => edge.id !== e.detail.id));
    };
    
    window.addEventListener('delete-edge', handleDeleteEdge as EventListener);
    return () => window.removeEventListener('delete-edge', handleDeleteEdge as EventListener);
  }, []);
  
  // Node/edge change handlers (intercept remove to delete custom state pair)
  const onNodesChange = useCallback((changes: NodeChange[]) => {
    const removeIds = new Set<string>();
    changes.forEach((c) => {
      if (c.type === 'remove' && c.id) {
        const node = nodes.find((n) => n.id === c.id);
        if (node?.type === 'custom_state_t' || node?.type === 'custom_state_t1') {
          const pairId = node.data?.statePairId;
          if (pairId) {
            const pair = nodes.find(
              (n) => n.id !== c.id && (n.type === 'custom_state_t' || n.type === 'custom_state_t1') && n.data?.statePairId === pairId
            );
            if (pair) removeIds.add(pair.id);
          }
        }
      }
    });
    const allChanges = [...changes];
    removeIds.forEach((id) => {
      if (!changes.some((c) => c.type === 'remove' && c.id === id)) {
        allChanges.push({ type: 'remove', id });
      }
    });
    setNodes((nds) => applyNodeChanges(allChanges, nds));
  }, [nodes]);
  
  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    setEdges((eds) => applyEdgeChanges(changes, eds));
  }, []);
  
  const onConnect = useCallback((connection: Connection) => {
    // Prevent multiple connections to the same input handle
    // Each input should only receive one signal
    const targetHandle = connection.targetHandle || 'input';
    const targetNodeId = connection.target;
    const sourceNodeId = connection.source;
    
    // Get source and target node info for shape validation
    const sourceNode = nodes.find(n => n.id === sourceNodeId);
    const targetNode = nodes.find(n => n.id === targetNodeId);
    const sourceShape = nodeShapes[sourceNodeId || ''];
    
    // Validate shapes for specific node types
    if (targetNode && sourceShape) {
      const targetType = targetNode.type || '';
      
      // Element-wise operations require compatible shapes
      if (['add', 'subtract', 'multiply', 'divide'].includes(targetType)) {
        // Get the other input's shape if connected
        const otherHandle = targetHandle === 'a' ? 'b' : 'a';
        const otherEdge = edges.find(
          e => e.target === targetNodeId && (e.targetHandle || 'input') === otherHandle
        );
        if (otherEdge) {
          const otherShape = nodeShapes[otherEdge.source];
          if (otherShape && !shapesCompatibleElementWise(sourceShape, otherShape)) {
            alert(`Shape mismatch! Cannot connect ${formatShape(sourceShape)} to ${formatShape(otherShape)} for element-wise operation.`);
            return;
          }
        }
      }
      
      // MatMul requires inner dimensions to match
      if (targetType === 'matmul') {
        const otherHandle = targetHandle === 'a' ? 'b' : 'a';
        const otherEdge = edges.find(
          e => e.target === targetNodeId && (e.targetHandle || 'input') === otherHandle
        );
        if (otherEdge) {
          const otherShape = nodeShapes[otherEdge.source];
          if (otherHandle === 'b' && sourceShape && otherShape) {
            // source is 'a', other is 'b': check a.cols == b.rows
            if (!shapesCompatibleMatMul(sourceShape, otherShape)) {
              alert(`Shape mismatch for MatMul! ${formatShape(sourceShape)} × ${formatShape(otherShape)} - inner dimensions must match.`);
              return;
            }
          } else if (otherHandle === 'a' && sourceShape && otherShape) {
            // source is 'b', other is 'a': check a.cols == b.rows
            if (!shapesCompatibleMatMul(otherShape, sourceShape)) {
              alert(`Shape mismatch for MatMul! ${formatShape(otherShape)} × ${formatShape(sourceShape)} - inner dimensions must match.`);
              return;
            }
          }
        }
      }
      
      // Concat requires all inputs to have same column count
      if (targetType === 'concat') {
        const numInputs = targetNode.data?.numInputs || 2;
        for (let i = 0; i < numInputs; i++) {
          const inputHandle = `input_${i}`;
          if (inputHandle === targetHandle) continue;
          
          const existingEdge = edges.find(
            e => e.target === targetNodeId && e.targetHandle === inputHandle
          );
          if (existingEdge) {
            const existingShape = nodeShapes[existingEdge.source];
            if (existingShape && sourceShape) {
              const [, sourceCols] = sourceShape;
              const [, existingCols] = existingShape;
              if (sourceCols !== 'L' && existingCols !== 'L' && sourceCols !== existingCols) {
                alert(`Shape mismatch for Concat! All inputs must have same column count. Got ${formatShape(sourceShape)} and ${formatShape(existingShape)}.`);
                return;
              }
            }
          }
        }
      }
    }
    
    // Check if this input is already connected
    const existingConnection = edges.find(
      e => e.target === targetNodeId && (e.targetHandle || 'input') === targetHandle
    );
    
    if (existingConnection) {
      // Replace existing connection instead of adding multiple
      setEdges((eds) => {
        const filtered = eds.filter(
          e => !(e.target === targetNodeId && (e.targetHandle || 'input') === targetHandle)
        );
        return addEdge({ ...connection, type: 'deletable' }, filtered);
      });
    } else {
      // Add edge with custom type for delete button
      setEdges((eds) => addEdge({ ...connection, type: 'deletable' }, eds));
    }
  }, [edges, nodes, nodeShapes]);
  
  
  // Delete selected edges
  const handleDeleteSelectedEdges = useCallback(() => {
    if (selectedEdges.length > 0) {
      setEdges((eds) => eds.filter((e) => !selectedEdges.includes(e.id)));
      setSelectedEdges([]);
    }
  }, [selectedEdges]);
  
  // Node selection
  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setSelectedEdges([]); // Deselect edges when clicking a node
  }, []);
  
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setSelectedEdges([]); // Deselect edges when clicking empty space
  }, []);
  
  // Edge click - toggle selection
  const onEdgeClickToggle = useCallback((_: React.MouseEvent, edge: Edge) => {
    setSelectedEdges((prev) => {
      if (prev.includes(edge.id)) {
        return []; // Deselect if already selected
      }
      return [edge.id]; // Select this edge
    });
    setSelectedNode(null);
  }, []);
  
  // Update node data (sync custom state pair when stateName/label changes)
  const handleUpdateNode = useCallback((id: string, newData: any) => {
    setNodes((nds) => {
      const node = nds.find((n) => n.id === id);
      const isCustomStateHalf = node?.type === 'custom_state_t' || node?.type === 'custom_state_t1';
      const pairId = node?.data?.statePairId ?? newData.statePairId;
      const stateName = newData.stateName ?? node?.data?.stateName ?? 'my_state';

      if (isCustomStateHalf && pairId) {
        return nds.map((n) => {
          if (n.id === id) return { ...n, data: newData };
          if ((n.type === 'custom_state_t' || n.type === 'custom_state_t1') && n.data?.statePairId === pairId) {
            const synced = { ...n.data, stateName, statePairId: pairId };
            synced.label = n.type === 'custom_state_t' ? `${stateName}_t` : `${stateName}_(t+1)`;
            return { ...n, data: synced };
          }
          return n;
        });
      }
      return nds.map((node) => (node.id === id ? { ...node, data: newData } : node));
    });
    setSelectedNode((prev) => (prev?.id === id ? { ...prev, data: newData } : prev));
  }, []);
  
  // Add new node (or pair for Custom State)
  const handleAddNode = useCallback((type: string) => {
    if (type === 'custom_state') {
      const pairId = crypto.randomUUID?.() ?? `pair-${Date.now()}`;
      const stateName = 'my_state';
      const baseX = 260 + Math.random() * 130;
      const baseY = 100 + Math.random() * 130;
      const nodeT: Node = {
        id: `custom_state_t-${Date.now()}`,
        type: 'custom_state_t',
        position: { x: baseX, y: baseY },
        data: {
          label: `${stateName}_t`,
          stateName,
          defaultValue: '0',
          shape: [1],
          statePairId: pairId,
        },
      };
      const nodeT1: Node = {
        id: `custom_state_t1-${Date.now()}`,
        type: 'custom_state_t1',
        position: { x: baseX + 220, y: baseY },
        data: {
          label: `${stateName}_(t+1)`,
          stateName,
          defaultValue: '0',
          shape: [1],
          statePairId: pairId,
        },
      };
      setNodes((nds) => [...nds, nodeT, nodeT1]);
      return;
    }

    const typeDef = NODE_TYPES[type as keyof typeof NODE_TYPES];
    if (!typeDef) return;

    const newNode: Node = {
      id: `${type}-${Date.now()}`,
      type,
      position: { x: 260 + Math.random() * 130, y: 100 + Math.random() * 130 },
      data: { ...typeDef.defaultData },
    };

    setNodes((nds) => [...nds, newNode]);
  }, []);
  
  // Delete selected node (and custom state pair if applicable)
  const handleDeleteSelected = useCallback(() => {
    if (!selectedNode) return;
    const pairId = selectedNode.data?.statePairId;
    const isCustomStateHalf = selectedNode.type === 'custom_state_t' || selectedNode.type === 'custom_state_t1';
    const toRemove = new Set<string>([selectedNode.id]);
    if (isCustomStateHalf && pairId) {
      const pair = nodes.find(
        (n) => n.id !== selectedNode.id && (n.type === 'custom_state_t' || n.type === 'custom_state_t1') && n.data?.statePairId === pairId
      );
      if (pair) toRemove.add(pair.id);
    }
    setNodes((nds) => nds.filter((n) => !toRemove.has(n.id)));
    setEdges((eds) => eds.filter((e) => !toRemove.has(e.source) && !toRemove.has(e.target)));
    setSelectedNode(null);
  }, [selectedNode, nodes]);
  
  // Generate code
  const handleGenerateCode = useCallback(async () => {
    const graph: VisualDesignGraph = {
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.type || 'unknown',
        position: n.position,
        data: n.data,
      })),
      edges: edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle || undefined,
        targetHandle: e.targetHandle || undefined,
      })),
      viewport: { x: 0, y: 0, zoom: 1 },
    };
    
    try {
      const result = await visualDesignerApi.generateCode(graph, symbol, timespan, multiplier);
      setGeneratedCode(result);
      setShowCode(true);
    } catch (e) {
      setGeneratedCode({
        code: '',
        errors: [e instanceof Error ? e.message : 'Unknown error'],
        warnings: [],
      });
      setShowCode(true);
    }
  }, [nodes, edges, symbol, timespan, multiplier]);
  
  // Save design and deploy as agent
  const handleSave = useCallback(async () => {
    const graph: VisualDesignGraph = {
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.type || 'unknown',
        position: n.position,
        data: n.data,
      })),
      edges: edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle || undefined,
        targetHandle: e.targetHandle || undefined,
      })),
      viewport: { x: 0, y: 0, zoom: 1 },
    };
    
    try {
      let saved: VisualDesign;
      if (designId) {
        saved = await visualDesignerApi.update(designId, {
          name: designName,
          graph_json: graph,
          symbol,
          primary_timespan: timespan,
          primary_multiplier: multiplier,
        });
      } else {
        saved = await visualDesignerApi.create({
          name: designName,
          graph_json: graph,
          symbol,
          primary_timespan: timespan,
          primary_multiplier: multiplier,
        });
        setDesignId(saved.id);
      }
      
      // Auto-deploy: create/update the agent with the same name as the design
      try {
        await visualDesignerApi.deploy(saved.id, designName, `Visual agent: ${designName}`);
      } catch (deployError) {
        console.warn('Auto-deploy failed:', deployError);
        // Don't fail the save if deploy fails
      }
      
      if (onSave) onSave(saved);
      alert('Agent saved and deployed!');
    } catch (e) {
      alert(`Failed to save: ${e instanceof Error ? e.message : 'Unknown error'}`);
    }
  }, [designId, designName, nodes, edges, symbol, timespan, multiplier, onSave]);
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'SELECT') {
          if (selectedNode) {
            handleDeleteSelected();
          } else if (selectedEdges.length > 0) {
            handleDeleteSelectedEdges();
          }
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNode, selectedEdges, handleDeleteSelected, handleDeleteSelectedEdges]);
  
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-[var(--bg-secondary)] border-b border-[var(--border-color)]">
        <div className="flex items-center gap-4">
          <input
            type="text"
            value={designName}
            onChange={(e) => setDesignName(e.target.value)}
            className="text-lg font-medium bg-transparent border-b border-transparent hover:border-[var(--border-color)] focus:border-[var(--accent-blue)] px-1"
            placeholder="Design name"
          />
          
          <div className="flex items-center gap-2 text-sm">
            <label className="text-[var(--text-secondary)]">Symbol:</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="w-20"
            />
            
            <label className="text-[var(--text-secondary)] ml-2">Timespan:</label>
            <select value={timespan} onChange={(e) => setTimespan(e.target.value)} className="w-24">
              <option value="minute">Minute</option>
              <option value="hour">Hour</option>
              <option value="day">Day</option>
              <option value="week">Week</option>
            </select>
            
            <label className="text-[var(--text-secondary)] ml-2">×</label>
            <input
              type="number"
              value={multiplier}
              onChange={(e) => setMultiplier(parseInt(e.target.value) || 1)}
              className="w-16"
              min={1}
            />
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {selectedNode && (
            <button 
              onClick={handleDeleteSelected}
              className="btn btn-secondary flex items-center gap-1 text-red-400"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
          )}
          <button 
            onClick={handleGenerateCode}
            className="btn btn-secondary flex items-center gap-1"
          >
            <Code className="w-4 h-4" />
            Generate
          </button>
          <button 
            onClick={handleSave}
            className="btn btn-primary flex items-center gap-1"
          >
            <Save className="w-4 h-4" />
            Save
          </button>
          <button onClick={onClose} className="btn btn-secondary">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Main area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Toolbox */}
        <Toolbox onAddNode={handleAddNode} />
        
        {/* Canvas */}
        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodesWithPreviews}
            edges={edges.map(e => ({ ...e, type: e.type || 'deletable', selected: selectedEdges.includes(e.id) }))}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onEdgeClick={onEdgeClickToggle}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            snapToGrid
            snapGrid={[15, 15]}
            deleteKeyCode={['Delete', 'Backspace']}
            defaultEdgeOptions={{
              type: 'deletable',
              style: { stroke: '#64748b', strokeWidth: 2 },
            }}
          >
            <Background color="#334155" gap={15} />
            <Controls />
            <MiniMap 
              nodeColor={(node) => {
                const typeDef = NODE_TYPES[node.type as keyof typeof NODE_TYPES];
                return typeDef?.color || '#64748b';
              }}
              maskColor="rgba(0,0,0,0.8)"
            />
          </ReactFlow>
        </div>
        
        {/* Properties panel */}
        <PropertiesPanel 
          selectedNode={selectedNode}
          onUpdateNode={handleUpdateNode}
          signals={signals}
        />
      </div>
      
      {/* Code panel overlay */}
      {showCode && generatedCode && (
        <CodePanel
          code={generatedCode.code}
          errors={generatedCode.errors}
          warnings={generatedCode.warnings}
          onClose={() => setShowCode(false)}
        />
      )}
    </div>
  );
}

// Main exported component with ReactFlowProvider wrapper
export function VisualDesigner({ isOpen, onClose, initialDesign, onSave }: VisualDesignerProps) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center">
      <div className="w-[95vw] h-[90vh] bg-[var(--bg-primary)] rounded-lg overflow-hidden shadow-2xl">
        <ReactFlowProvider>
          <DesignerCanvas
            initialDesign={initialDesign}
            onSave={onSave}
            onClose={onClose}
          />
        </ReactFlowProvider>
      </div>
    </div>
  );
}

export default VisualDesigner;
