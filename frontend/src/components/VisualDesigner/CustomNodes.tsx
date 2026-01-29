/**
 * Custom node components for ReactFlow.
 * Each node type has its own component with sparklines, inputs/outputs, and styling.
 */

import { memo, useCallback, useEffect, useState } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { getNodeTypeDef, CATEGORY_COLORS } from './nodeTypes';
import { visualDesignerApi } from '../../api/client';

// Sparkline component for visualizing signal data
function Sparkline({ values, color = '#22c55e' }: { values: number[]; color?: string }) {
  if (!values || values.length === 0) {
    return <div className="h-8 flex items-center justify-center text-xs text-gray-500">No data</div>;
  }
  
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  
  const width = 100;
  const height = 24;
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width;
    const y = height - ((v - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');
  
  return (
    <svg width={width} height={height} className="sparkline">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        points={points}
      />
    </svg>
  );
}

// Base node component that all node types use
interface BaseNodeProps extends NodeProps {
  nodeType: string;
}

function BaseNode({ id, data, selected, nodeType }: BaseNodeProps) {
  const typeDef = getNodeTypeDef(nodeType);
  const [sparklineData, setSparklineData] = useState<number[]>([]);
  
  // Fetch sparkline data for signal nodes
  useEffect(() => {
    if (nodeType === 'signal' && data.signalId) {
      visualDesignerApi.getSignalPreview(data.signalId, 20)
        .then(preview => setSparklineData(preview.values))
        .catch(() => setSparklineData([]));
    }
  }, [nodeType, data.signalId]);
  
  if (!typeDef) {
    return <div className="p-2 bg-gray-700 rounded">Unknown: {nodeType}</div>;
  }
  
  const borderColor = selected ? '#fff' : typeDef.color;
  
  return (
    <div
      className="min-w-[140px] rounded-lg shadow-lg"
      style={{
        background: '#1e293b',
        border: `2px solid ${borderColor}`,
      }}
    >
      {/* Header */}
      <div 
        className="px-3 py-1.5 rounded-t-md text-white text-sm font-medium"
        style={{ background: typeDef.color }}
      >
        {data.label || typeDef.label}
      </div>
      
      {/* Body */}
      <div className="px-3 py-2">
        {/* Signal-specific: show signal ID and sparkline */}
        {nodeType === 'signal' && (
          <>
            <div className="text-xs text-gray-400 mb-1 truncate">
              {data.signalId || 'No signal selected'}
            </div>
            <Sparkline values={sparklineData} color={typeDef.color} />
          </>
        )}
        
        {/* Constant-specific: show value */}
        {nodeType === 'constant' && (
          <div className="text-xs text-gray-300">
            Value: {data.value ?? 0}
            {data.shape && data.shape.length > 1 && (
              <span className="ml-2 text-gray-500">Shape: [{data.shape.join('×')}]</span>
            )}
          </div>
        )}
        
        {/* Variable-specific: show shape and init type */}
        {nodeType === 'variable' && (
          <div className="text-xs text-gray-300">
            <div>{data.name || 'weight'}</div>
            <div className="text-gray-500">
              Shape: [{(data.shape || [1]).join('×')}] | {data.initType || 'random'}
            </div>
          </div>
        )}
        
        {/* Slice-specific: show N */}
        {nodeType === 'slice' && (
          <div className="text-xs text-gray-300">Last {data.n || 10} elements</div>
        )}
        
        {/* Clip-specific: show range */}
        {nodeType === 'clip' && (
          <div className="text-xs text-gray-300">
            Range: [{data.min ?? -1}, {data.max ?? 1}]
          </div>
        )}
        
        {/* Rolling ops: show window */}
        {(nodeType === 'rolling_mean' || nodeType === 'rolling_std') && (
          <div className="text-xs text-gray-300">Window: {data.window || 10}</div>
        )}
        
        {/* Linear layer: show dimensions */}
        {nodeType === 'linear' && (
          <div className="text-xs text-gray-300">
            {data.inFeatures || 10} → {data.outFeatures || 1}
          </div>
        )}
        
        {/* LSTM: show config */}
        {nodeType === 'lstm' && (
          <div className="text-xs text-gray-300">
            Hidden: {data.hiddenSize || 32}
          </div>
        )}
        
        {/* Conv1D: show config */}
        {nodeType === 'conv1d' && (
          <div className="text-xs text-gray-300">
            {data.inChannels || 1} → {data.outChannels || 16}, k={data.kernelSize || 3}
          </div>
        )}
        
        {/* Output node */}
        {nodeType === 'output' && (
          <div className="text-xs text-gray-400">{data.description || 'Position delta'}</div>
        )}
      </div>
      
      {/* Input handles */}
      {typeDef.inputs.map((input, i) => (
        <Handle
          key={`input-${input.name}`}
          type="target"
          position={Position.Left}
          id={input.name}
          style={{
            top: `${30 + (i * 20) + 20}px`,
            background: '#64748b',
            width: 10,
            height: 10,
            border: '2px solid #1e293b',
          }}
          title={input.name}
        />
      ))}
      
      {/* Output handles */}
      {typeDef.outputs.map((output, i) => (
        <Handle
          key={`output-${output.name}`}
          type="source"
          position={Position.Right}
          id={output.name}
          style={{
            top: `${30 + (i * 20) + 20}px`,
            background: typeDef.color,
            width: 10,
            height: 10,
            border: '2px solid #1e293b',
          }}
          title={output.name}
        />
      ))}
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
