/**
 * Custom node components for ReactFlow.
 * Each node type has its own component with sparklines, inputs/outputs, and styling.
 */

import { memo, useEffect, useState, useMemo } from 'react';
import { Handle, Position, NodeProps, NodeResizer, useStore } from '@xyflow/react';
import { getNodeTypeDef } from './nodeTypes';
import { visualDesignerApi } from '../../api/client';

// Sparkline component for visualizing signal/vector data
function Sparkline({ values, color = '#22c55e', width = 100, height = 28, showLabels = true }: { 
  values: number[]; 
  color?: string;
  width?: number;
  height?: number;
  showLabels?: boolean;
}) {
  if (!values || values.length === 0) {
    return (
      <div 
        className="flex items-center justify-center text-xs text-gray-500 bg-gray-800/50 rounded"
        style={{ width, height }}
      >
        No data
      </div>
    );
  }
  
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  
  const points = values.map((v, i) => {
    const x = (i / Math.max(values.length - 1, 1)) * width;
    const y = height - 2 - ((v - min) / range) * (height - 4);
    return `${x},${y}`;
  }).join(' ');
  
  return (
    <div className="bg-gray-800/50 rounded p-0.5" style={{ width: width + 4 }}>
      <svg width={width} height={height}>
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          points={points}
        />
        {/* Min/Max labels */}
        {showLabels && (
          <>
            <text x={width - 2} y={10} fontSize={8} fill="#9ca3af" textAnchor="end">
              {max.toFixed(1)}
            </text>
            <text x={width - 2} y={height - 2} fontSize={8} fill="#9ca3af" textAnchor="end">
              {min.toFixed(1)}
            </text>
          </>
        )}
      </svg>
    </div>
  );
}

// Generate demo signal data when API fails or returns empty
function generateDemoSignalData(signalId: string): number[] {
  // Use signal ID to create unique but deterministic data
  const seed = signalId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const basePrice = 100 + (seed % 500); // Base price between 100-600
  
  return Array.from({ length: 20 }, (_, i) => {
    const t = i / 20;
    // Generate realistic-looking price data with trend and noise
    return basePrice + 
      Math.sin(t * 4 + seed * 0.1) * basePrice * 0.05 +  // Wave pattern
      Math.cos(t * 7) * basePrice * 0.02 +  // Smaller oscillation
      (seed % 2 === 0 ? t * basePrice * 0.03 : -t * basePrice * 0.02) + // Trend
      (Math.random() - 0.5) * basePrice * 0.01; // Small noise
  });
}

// Generate sample data that simulates the result of an operation
function generateComputedSparkline(
  operation: string, 
  nodeId: string,
  params: Record<string, any> = {}
): number[] {
  // Use nodeId to create unique but deterministic seed
  const seed = nodeId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  
  // Base signal - simulated price-like data
  const baseSignal = Array.from({ length: 20 }, (_, i) => {
    const t = i / 20;
    return 100 + Math.sin(t * 6 + seed * 0.1) * 10 + Math.cos(t * 3) * 5 + (seed % 10);
  });
  
  switch (operation) {
    case 'slice':
      const n = params.n || 10;
      return baseSignal.slice(-Math.min(n, 20));
      
    case 'add':
      return baseSignal.map((v, i) => v + 5 + Math.sin(i * 0.5 + seed) * 2);
      
    case 'subtract':
      return baseSignal.map((v, i) => v - 5 - Math.sin(i * 0.5 + seed) * 2);
      
    case 'multiply':
      return baseSignal.map(v => v * 1.1);
      
    case 'divide':
      return baseSignal.map(v => v / 1.1);
      
    case 'normalize':
      const mean = baseSignal.reduce((a, b) => a + b, 0) / baseSignal.length;
      const std = Math.sqrt(baseSignal.reduce((a, b) => a + (b - mean) ** 2, 0) / baseSignal.length);
      return baseSignal.map(v => (v - mean) / (std || 1));
      
    case 'clip':
      const minVal = params.min ?? -1;
      const maxVal = params.max ?? 1;
      const normalized = baseSignal.map(v => (v - 100) / 10);
      return normalized.map(v => Math.max(minVal, Math.min(maxVal, v)));
      
    case 'rolling_mean':
      const window = params.window || 5;
      return baseSignal.map((_, i, arr) => {
        const start = Math.max(0, i - window + 1);
        const slice = arr.slice(start, i + 1);
        return slice.reduce((a, b) => a + b, 0) / slice.length;
      });
      
    case 'rolling_std':
      const w = params.window || 5;
      return baseSignal.map((_, i, arr) => {
        const start = Math.max(0, i - w + 1);
        const slice = arr.slice(start, i + 1);
        const m = slice.reduce((a, b) => a + b, 0) / slice.length;
        return Math.sqrt(slice.reduce((a, b) => a + (b - m) ** 2, 0) / slice.length);
      });
      
    case 'mean':
    case 'sum':
    case 'std':
    case 'min':
    case 'max':
      // These reduce to scalar, show flat line at result
      const result = operation === 'mean' ? baseSignal.reduce((a, b) => a + b, 0) / baseSignal.length
        : operation === 'sum' ? baseSignal.reduce((a, b) => a + b, 0) / 100
        : operation === 'std' ? Math.sqrt(baseSignal.reduce((a, b) => a + (b - 100) ** 2, 0) / baseSignal.length)
        : operation === 'min' ? Math.min(...baseSignal) - 90
        : Math.max(...baseSignal) - 90;
      return Array(20).fill(result);
      
    case 'relu':
      return baseSignal.map(v => Math.max(0, (v - 100)));
      
    case 'tanh':
      return baseSignal.map(v => Math.tanh((v - 100) / 10));
      
    case 'sigmoid':
      return baseSignal.map(v => 1 / (1 + Math.exp(-(v - 100) / 5)));
      
    case 'linear':
      return baseSignal.map((v, i) => (v - 100) * 0.5 + Math.sin(i * 0.3 + seed) * 2);
      
    case 'concat':
      return [...baseSignal.slice(0, 10), ...baseSignal.slice(10).map(v => v + 10)];
      
    default:
      return baseSignal;
  }
}

// Base node component that all node types use
interface BaseNodeProps extends NodeProps {
  nodeType: string;
}

// Categories of nodes that should show computed sparklines
const COMPUTED_SPARKLINE_NODES = [
  'slice', 'concat', 'add', 'subtract', 'multiply', 'divide',
  'normalize', 'clip', 'rolling_mean', 'rolling_std', 'mean', 'sum', 'std',
  'min', 'max', 'linear', 'relu', 'tanh', 'sigmoid'
];

function BaseNode({ id, data, selected, nodeType }: BaseNodeProps) {
  const typeDef = getNodeTypeDef(nodeType);
  const [signalSparklineData, setSignalSparklineData] = useState<number[]>([]);
  
  // Fetch sparkline data for signal nodes from API
  useEffect(() => {
    if (nodeType === 'signal' && data.signalId) {
      console.log(`[Signal Node ${id}] Fetching preview for signal: ${data.signalId}`);
      visualDesignerApi.getSignalPreview(data.signalId, 20)
        .then(preview => {
          console.log(`[Signal Node ${id}] Got preview:`, preview);
          if (preview && preview.values && preview.values.length > 0) {
            setSignalSparklineData(preview.values);
          } else {
            console.warn(`[Signal Node ${id}] Preview has no values, using demo data`);
            // Use demo data as fallback
            setSignalSparklineData(generateDemoSignalData(data.signalId));
          }
        })
        .catch((err) => {
          console.error(`[Signal Node ${id}] Failed to fetch signal preview:`, err);
          // Use demo data as fallback on error
          setSignalSparklineData(generateDemoSignalData(data.signalId));
        });
    } else if (nodeType === 'signal') {
      // Reset if no signal selected
      setSignalSparklineData([]);
    }
  }, [nodeType, data.signalId, id]);
  
  // Generate computed sparkline data for operation nodes
  const computedSparkline = useMemo(() => {
    if (COMPUTED_SPARKLINE_NODES.includes(nodeType)) {
      return generateComputedSparkline(nodeType, id, data);
    }
    return [];
  }, [nodeType, id, data.n, data.window, data.min, data.max]);
  
  if (!typeDef) {
    return <div className="p-2 bg-gray-700 rounded">Unknown: {nodeType}</div>;
  }
  
  const borderColor = selected ? '#fff' : typeDef.color;
  const numInputs = typeDef.inputs.length;
  const numOutputs = typeDef.outputs.length;
  const maxHandles = Math.max(numInputs, numOutputs, 1);
  
  // Calculate minimum height based on number of handles
  const showSparkline = nodeType === 'signal' || COMPUTED_SPARKLINE_NODES.includes(nodeType) || nodeType === 'output';
  const baseBodyHeight = showSparkline ? 70 : 40;
  const handleHeight = maxHandles * 26;
  const minBodyHeight = Math.max(baseBodyHeight, handleHeight);
  
  // Don't show resizer for output node to avoid the white box issue
  const showResizer = selected && nodeType !== 'output';
  
  return (
    <div
      className="min-w-[160px] rounded-lg shadow-lg relative"
      style={{
        background: '#1e293b',
        border: `2px solid ${borderColor}`,
      }}
    >
      {/* Resizer - only visible when selected, not for output nodes */}
      {showResizer && (
        <NodeResizer
          color={typeDef.color}
          isVisible={true}
          minWidth={140}
          minHeight={80}
        />
      )}
      
      {/* Header */}
      <div 
        className="px-3 py-1.5 rounded-t-md text-white text-sm font-medium flex items-center justify-between"
        style={{ background: typeDef.color }}
      >
        <span>{data.label || typeDef.label}</span>
        {/* Frequency badge for signals */}
        {nodeType === 'signal' && (
          <span className="text-xs bg-black/30 px-1.5 py-0.5 rounded">
            {data.frequency || '1D'}
          </span>
        )}
      </div>
      
      {/* Body */}
      <div className="px-3 py-2" style={{ minHeight: minBodyHeight }}>
        {/* Signal-specific: show signal ID, frequency, and ACTUAL sparkline */}
        {nodeType === 'signal' && (
          <>
            <div className="text-xs text-gray-400 mb-1 truncate">
              {data.signalId || 'No signal selected'}
            </div>
            <Sparkline 
              values={signalSparklineData} 
              color={typeDef.color} 
              width={120} 
              height={32}
            />
          </>
        )}
        
        {/* Constant-specific: show value and flat sparkline */}
        {nodeType === 'constant' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1">Value: {data.value ?? 0}</div>
            {data.shape && data.shape.length > 1 && (
              <div className="text-gray-500 mb-1">Shape: [{data.shape.join('×')}]</div>
            )}
            <Sparkline 
              values={Array(20).fill(data.value ?? 0)} 
              color={typeDef.color} 
              width={100} 
              height={24}
              showLabels={false}
            />
          </div>
        )}
        
        {/* Variable-specific: show shape and random sparkline */}
        {nodeType === 'variable' && (
          <div className="text-xs text-gray-300">
            <div>{data.name || 'weight'}</div>
            <div className="text-gray-500 mb-1">
              [{(data.shape || [1]).join('×')}] | {data.initType || 'random'}
            </div>
            <Sparkline 
              values={generateComputedSparkline('normalize', id, data)} 
              color={typeDef.color} 
              width={100} 
              height={24}
            />
          </div>
        )}
        
        {/* Slice-specific: show N and computed result */}
        {nodeType === 'slice' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1">Last {data.n || 10} elements</div>
            <Sparkline values={computedSparkline} color={typeDef.color} width={100} height={28} />
          </div>
        )}
        
        {/* Concat node */}
        {nodeType === 'concat' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500">input1 →</div>
            <div className="text-gray-500 mb-1">input2 →</div>
            <Sparkline values={computedSparkline} color={typeDef.color} width={100} height={28} />
          </div>
        )}
        
        {/* Binary ops: add, subtract, multiply, divide */}
        {['add', 'subtract', 'multiply', 'divide'].includes(nodeType) && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500">a →</div>
            <div className="text-gray-500 mb-1">b →</div>
            <Sparkline values={computedSparkline} color={typeDef.color} width={100} height={28} />
          </div>
        )}
        
        {/* MatMul */}
        {nodeType === 'matmul' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500">a →</div>
            <div className="text-gray-500">b →</div>
          </div>
        )}
        
        {/* Aggregation ops: mean, sum, std, min, max */}
        {['mean', 'sum', 'std', 'min', 'max'].includes(nodeType) && (
          <div className="text-xs text-gray-300">
            <div className="mb-1">Axis: {data.axis ?? 'all'}</div>
            <Sparkline values={computedSparkline} color={typeDef.color} width={100} height={28} />
          </div>
        )}
        
        {/* Normalize */}
        {nodeType === 'normalize' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1">Z-score normalization</div>
            <Sparkline values={computedSparkline} color={typeDef.color} width={100} height={28} />
          </div>
        )}
        
        {/* Clip-specific: show range */}
        {nodeType === 'clip' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1">[{data.min ?? -1}, {data.max ?? 1}]</div>
            <Sparkline values={computedSparkline} color={typeDef.color} width={100} height={28} />
          </div>
        )}
        
        {/* Rolling ops: show window */}
        {(nodeType === 'rolling_mean' || nodeType === 'rolling_std') && (
          <div className="text-xs text-gray-300">
            <div className="mb-1">Window: {data.window || 10}</div>
            <Sparkline values={computedSparkline} color={typeDef.color} width={100} height={28} />
          </div>
        )}
        
        {/* Linear layer: show dimensions */}
        {nodeType === 'linear' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1">{data.inFeatures || 10} → {data.outFeatures || 1}</div>
            <Sparkline values={computedSparkline} color={typeDef.color} width={100} height={28} />
          </div>
        )}
        
        {/* Activation functions */}
        {['relu', 'tanh', 'sigmoid', 'softmax'].includes(nodeType) && (
          <div className="text-xs text-gray-300">
            <Sparkline values={computedSparkline} color={typeDef.color} width={100} height={28} />
          </div>
        )}
        
        {/* LSTM: show config */}
        {nodeType === 'lstm' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1">Hidden: {data.hiddenSize || 32}</div>
            <div className="text-gray-500">output →</div>
            <div className="text-gray-500">hidden →</div>
          </div>
        )}
        
        {/* Conv1D: show config */}
        {nodeType === 'conv1d' && (
          <div className="text-xs text-gray-300">
            <div>{data.inChannels || 1} → {data.outChannels || 16}</div>
            <div className="text-gray-500 mb-1">kernel: {data.kernelSize || 3}</div>
          </div>
        )}
        
        {/* Output node - show computed output value */}
        {nodeType === 'output' && (
          <div className="text-xs">
            <div className="text-gray-400 mb-1">{data.description || 'Position delta'}</div>
            <div className="text-gray-500 mb-1">input →</div>
            <div className="bg-gray-800/50 rounded p-2 text-center">
              <span className="text-lg font-mono text-green-400">
                {data.computedValue !== undefined ? data.computedValue.toFixed(2) : '0.00'}
              </span>
              <div className="text-gray-500 text-xs mt-1">shares</div>
            </div>
          </div>
        )}
      </div>
      
      {/* Input handles - positioned relative to body content */}
      {typeDef.inputs.map((input, i) => {
        // Calculate position: header (32px) + offset into body
        const bodyOffset = 36 + 16 + (i * 26);
        return (
          <Handle
            key={`input-${input.name}`}
            type="target"
            position={Position.Left}
            id={input.name}
            style={{
              top: bodyOffset,
              background: '#64748b',
              width: 12,
              height: 12,
              border: '2px solid #1e293b',
            }}
            title={input.name}
          />
        );
      })}
      
      {/* Output handles */}
      {typeDef.outputs.map((output, i) => {
        const bodyOffset = 36 + 16 + (i * 26);
        return (
          <Handle
            key={`output-${output.name}`}
            type="source"
            position={Position.Right}
            id={output.name}
            style={{
              top: bodyOffset,
              background: typeDef.color,
              width: 12,
              height: 12,
              border: '2px solid #1e293b',
            }}
            title={output.name}
          />
        );
      })}
    </div>
  );
}

// Create individual node components for each type
export const SignalNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="signal" />
));

export const ConstantNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="constant" />
));

export const VariableNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="variable" />
));

export const SliceNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="slice" />
));

export const ConcatNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="concat" />
));

export const AddNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="add" />
));

export const SubtractNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="subtract" />
));

export const MultiplyNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="multiply" />
));

export const DivideNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="divide" />
));

export const MatmulNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="matmul" />
));

export const MeanNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="mean" />
));

export const SumNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="sum" />
));

export const StdNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="std" />
));

export const MinNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="min" />
));

export const MaxNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="max" />
));

export const NormalizeNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="normalize" />
));

export const ClipNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="clip" />
));

export const RollingMeanNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="rolling_mean" />
));

export const RollingStdNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="rolling_std" />
));

export const RsiNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="rsi" />
));

export const MacdNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="macd" />
));

export const BollingerNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="bollinger" />
));

export const LinearNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="linear" />
));

export const ReluNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="relu" />
));

export const TanhNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="tanh" />
));

export const SigmoidNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="sigmoid" />
));

export const SoftmaxNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="softmax" />
));

export const LstmNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="lstm" />
));

export const Conv1dNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="conv1d" />
));

export const OutputNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="output" />
));

// Export all node types as a map for ReactFlow
export const nodeTypes = {
  signal: SignalNode,
  constant: ConstantNode,
  variable: VariableNode,
  slice: SliceNode,
  concat: ConcatNode,
  add: AddNode,
  subtract: SubtractNode,
  multiply: MultiplyNode,
  divide: DivideNode,
  matmul: MatmulNode,
  mean: MeanNode,
  sum: SumNode,
  std: StdNode,
  min: MinNode,
  max: MaxNode,
  normalize: NormalizeNode,
  clip: ClipNode,
  rolling_mean: RollingMeanNode,
  rolling_std: RollingStdNode,
  rsi: RsiNode,
  macd: MacdNode,
  bollinger: BollingerNode,
  linear: LinearNode,
  relu: ReluNode,
  tanh: TanhNode,
  sigmoid: SigmoidNode,
  softmax: SoftmaxNode,
  lstm: LstmNode,
  conv1d: Conv1dNode,
  output: OutputNode,
};
