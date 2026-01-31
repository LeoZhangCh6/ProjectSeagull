/**
 * Custom node components for ReactFlow.
 * Each node type has its own component with sparklines, inputs/outputs, and styling.
 * 
 * Preview data is now computed by the parent component and passed via node.data._preview
 */

import { memo } from 'react';
import { Handle, Position, NodeProps, NodeResizer } from '@xyflow/react';
import { getNodeTypeDef } from './nodeTypes';

// Preview data type (injected by parent component)
type PreviewData = { type: 'tensor'; values: number[] } | { type: 'scalar'; value: number };

// Shape type
type ShapeDim = number | 'L';
type Shape = [ShapeDim, ShapeDim];

// Format shape for display
function formatShape(shape: Shape | null): string {
  if (!shape) return '(?, ?)';
  const [rows, cols] = shape;
  return `(${rows}, ${cols})`;
}

// Sparkline component for visualizing tensor/1D data
function Sparkline({ values, color = '#22c55e', width = 130, height = 28, showLabels = true }: { 
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
              {max.toFixed(2)}
            </text>
            <text x={width - 2} y={height - 2} fontSize={8} fill="#9ca3af" textAnchor="end">
              {min.toFixed(2)}
            </text>
          </>
        )}
      </svg>
    </div>
  );
}

// Scalar value display component
function ScalarDisplay({ value, color = '#22c55e', label }: { 
  value: number; 
  color?: string;
  label?: string;
}) {
  // Format the value based on magnitude
  const formatValue = (v: number): string => {
    if (Math.abs(v) >= 1000) return v.toFixed(0);
    if (Math.abs(v) >= 100) return v.toFixed(1);
    if (Math.abs(v) >= 1) return v.toFixed(2);
    return v.toFixed(4);
  };
  
  return (
    <div className="bg-gray-800/50 rounded p-2 text-center">
      <span 
        className="text-lg font-mono"
        style={{ color }}
      >
        {formatValue(value)}
      </span>
      {label && <div className="text-gray-500 text-xs mt-1">{label}</div>}
    </div>
  );
}

// Universal preview display - shows sparkline for tensors, scalar for scalars
function PreviewDisplay({ 
  preview, 
  color, 
  width = 130, 
  height = 28,
  scalarLabel 
}: { 
  preview?: PreviewData;
  color: string;
  width?: number;
  height?: number;
  scalarLabel?: string;
}) {
  if (!preview) {
    return (
      <div 
        className="flex items-center justify-center text-xs text-gray-500 bg-gray-800/50 rounded"
        style={{ width, height }}
      >
        Not connected
      </div>
    );
  }
  
  if (preview.type === 'scalar') {
    return <ScalarDisplay value={preview.value} color={color} label={scalarLabel} />;
  }
  
  return <Sparkline values={preview.values} color={color} width={width} height={height} />;
}

// Base node component that all node types use
interface BaseNodeProps extends NodeProps {
  nodeType: string;
}

function BaseNode({ id, data, selected, nodeType }: BaseNodeProps) {
  const typeDef = getNodeTypeDef(nodeType);
  
  // Get preview data and shape from parent-computed values
  const preview = data._preview as PreviewData | undefined;
  const shape = data._shape as Shape | null;
  
  if (!typeDef) {
    return <div className="p-2 bg-gray-700 rounded">Unknown: {nodeType}</div>;
  }
  
  const borderColor = selected ? '#fff' : typeDef.color;
  // For concat, use dynamic numInputs; for others, use typeDef
  const numInputs = nodeType === 'concat' ? (data.numInputs || 2) : typeDef.inputs.length;
  const numOutputs = typeDef.outputs.length;
  const maxHandles = Math.max(numInputs, numOutputs, 1);
  
  // Calculate minimum height based on number of handles
  // Show preview for all nodes that have outputs
  const hasPreview = typeDef.outputs.length > 0 || nodeType === 'output';
  const baseBodyHeight = hasPreview ? 70 : 40;
  const handleHeight = maxHandles * 26;
  const minBodyHeight = Math.max(baseBodyHeight, handleHeight);
  
  // Don't show resizer for output node to avoid the white box issue
  const showResizer = selected && nodeType !== 'output';
  
  return (
    <div
      className="min-w-[208px] rounded-lg shadow-lg relative"
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
        {/* Shape badge */}
        <span className="text-xs bg-black/30 px-1.5 py-0.5 rounded font-mono">
          {formatShape(shape)}
        </span>
      </div>
      
      {/* Body */}
      <div className="px-3 py-2" style={{ minHeight: minBodyHeight }}>
        {/* Signal-specific: show signal ID and preview */}
        {nodeType === 'signal' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-400 mb-1 truncate">
              {data.signalId || 'No signal selected'}
            </div>
            <div className="text-gray-500 text-[10px] mb-1">
              {data.frequency || '1D'}
            </div>
            <PreviewDisplay preview={preview} color={typeDef.color} width={156} height={32} />
          </div>
        )}
        
        {/* Constant-specific: show value and preview */}
        {nodeType === 'constant' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1">Value: {data.value ?? 0}</div>
            {data.shape && data.shape.length > 1 && (
              <div className="text-gray-500 mb-1">Shape: [{data.shape.join('×')}]</div>
            )}
            <PreviewDisplay preview={preview} color={typeDef.color} width={130} height={24} />
          </div>
        )}
        
        {/* Variable-specific: show shape and preview */}
        {nodeType === 'variable' && (
          <div className="text-xs text-gray-300">
            <div>{data.name || 'weight'}</div>
            <div className="text-gray-500 mb-1">
              [{(data.shape || [1]).join('×')}] | {data.initType || 'zeros'}
            </div>
            {/* Only show preview for 1D variables */}
            {(data.shape?.length ?? 1) <= 1 && (
              <PreviewDisplay preview={preview} color={typeDef.color} width={130} height={24} />
            )}
            {(data.shape?.length ?? 1) > 1 && (
              <div className="text-gray-500 italic">Multi-dim (no preview)</div>
            )}
          </div>
        )}
        
        {/* Range-specific: show parameters and preview */}
        {nodeType === 'range' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">
              {data.mode === 'end' 
                ? `N=${data.n || 10}, [${data.start ?? 0} → ${data.end ?? 10}]`
                : `N=${data.n || 10}, start=${data.start ?? 0}, step=${data.step ?? 1}`
              }
            </div>
            <PreviewDisplay preview={preview} color={typeDef.color} width={130} height={28} />
          </div>
        )}
        
        {/* Agent State: show 3 outputs */}
        {nodeType === 'agent_state' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1 space-y-0.5">
              <div>Shares: {data.demoShares ?? 10}</div>
              <div>Equity: ${(data.demoEquity ?? 100000).toLocaleString()}</div>
              <div>Cash: ${((data.demoEquity ?? 100000) - (data.demoShares ?? 10) * 100).toLocaleString()}</div>
            </div>
          </div>
        )}
        
        {/* Agent Equity Curve */}
        {nodeType === 'agent_equity_curve' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">
              History: {data.historyLength ?? 50} bars
            </div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Custom State */}
        {nodeType === 'custom_state' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1 font-mono text-[10px]">
              {data.stateName || 'my_state'}
            </div>
            <div className="text-gray-600 text-[10px] mb-1">
              default: {data.defaultValue || '0'}
            </div>
            {shape && shape[0] === 1 && shape[1] === 1 ? (
              <ScalarDisplay value={preview?.type === 'scalar' ? preview.value : 0} color={typeDef.color} />
            ) : (
              <PreviewDisplay preview={preview} color={typeDef.color} />
            )}
          </div>
        )}
        
        {/* Sign function */}
        {nodeType === 'sign' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">sign(x): 1 if x{'>'} 0, else -1</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Sin function */}
        {nodeType === 'sin' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">sin(x)</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Cos function */}
        {nodeType === 'cos' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">cos(x)</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Slice-specific: show window range and live preview */}
        {nodeType === 'slice' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">
              [{-(data.n || 10)} : {(data.m ?? 0) === 0 ? 'end' : -(data.m ?? 0)}]
            </div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Concat node - dynamic inputs */}
        {nodeType === 'concat' && (
          <div className="text-xs text-gray-300">
            {Array.from({ length: data.numInputs || 2 }, (_, i) => (
              <div key={i} className="text-gray-500">input_{i} →</div>
            ))}
            <div className="mb-1"></div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Binary ops: add, subtract, multiply, divide */}
        {['add', 'subtract', 'multiply', 'divide'].includes(nodeType) && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500">a →</div>
            <div className="text-gray-500 mb-1">b →</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Transpose */}
        {nodeType === 'transpose' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">Swaps (R, C) → (C, R)</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* MatMul - outputs scalar (dot product result) */}
        {nodeType === 'matmul' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500">a →</div>
            <div className="text-gray-500 mb-1">b →</div>
            <PreviewDisplay preview={preview} color={typeDef.color} scalarLabel="result" />
          </div>
        )}
        
        {/* Aggregation ops: mean, sum, min, max - output scalar */}
        {['mean', 'sum', 'min', 'max'].includes(nodeType) && (
          <div className="text-xs text-gray-300">
            <PreviewDisplay preview={preview} color={typeDef.color} scalarLabel={nodeType} />
          </div>
        )}
        
        {/* Std Dev - show population vs sample */}
        {nodeType === 'std' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">
              {data.ddof === 1 ? 'Sample' : 'Population'}
            </div>
            <PreviewDisplay preview={preview} color={typeDef.color} scalarLabel="std dev" />
          </div>
        )}
        
        {/* Variance - show population vs sample */}
        {nodeType === 'variance' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">
              {data.ddof === 1 ? 'Sample' : 'Population'}
            </div>
            <PreviewDisplay preview={preview} color={typeDef.color} scalarLabel="variance" />
          </div>
        )}
        
        {/* Normalize */}
        {nodeType === 'normalize' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">Z-score normalization</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Clip-specific: show range */}
        {nodeType === 'clip' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">[{data.min ?? -1}, {data.max ?? 1}]</div>
            {/* Show scalar if shape is (1,1), otherwise sparkline */}
            {shape && shape[0] === 1 && shape[1] === 1 ? (
              <ScalarDisplay value={preview?.type === 'scalar' ? preview.value : (preview?.type === 'tensor' ? preview.values[0] : 0)} color={typeDef.color} />
            ) : (
              <PreviewDisplay preview={preview} color={typeDef.color} />
            )}
          </div>
        )}
        
        {/* Rolling ops: show window */}
        {(nodeType === 'rolling_mean' || nodeType === 'rolling_std') && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">Window: {data.window || 10}</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Shift: show n and fill mode */}
        {nodeType === 'shift' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">
              Shift: {data.n || 1}, {
                (data.fillMode || 'none') === 'none' ? 'no pad' :
                data.fillMode === 'first' ? 'fill: first' : 'fill: 0'
              }
            </div>
            {(data.fillMode || 'none') === 'none' && (
              <div className="mb-1 text-gray-600 text-[10px]">
                Output: len - {data.n || 1}
              </div>
            )}
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Shift-Diff: show n and mode */}
        {nodeType === 'shift_diff' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">
              Lag: {data.n || 1}, {data.diffMode || 'raw'}
            </div>
            <div className="mb-1 text-gray-600 text-[10px]">
              Output: len - {data.n || 1}
            </div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Conv1D Custom: show kernel and padding */}
        {nodeType === 'conv1d_custom' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500 truncate font-mono text-[10px]">
              kernel: [{data.kernel || '0.25, 0.5, 0.25'}]
            </div>
            <div className="mb-1 text-gray-600 text-[10px]">
              {data.padding === 'same' ? 'Same (preserve len)' : 'Valid (shorter)'}
            </div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Linear layer: show dimensions */}
        {nodeType === 'linear' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">{data.inFeatures || 10} → {data.outFeatures || 1}</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Activation functions */}
        {['relu', 'tanh', 'sigmoid', 'softmax'].includes(nodeType) && (
          <div className="text-xs text-gray-300">
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* LSTM: show config */}
        {nodeType === 'lstm' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">Hidden: {data.hiddenSize || 32}</div>
            <div className="text-gray-500">output →</div>
            <div className="text-gray-500">hidden →</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Conv1D: show config */}
        {nodeType === 'conv1d' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500">{data.inChannels || 1} → {data.outChannels || 16}</div>
            <div className="text-gray-500 mb-1">kernel: {data.kernelSize || 3}</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* RSI indicator */}
        {nodeType === 'rsi' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">Period: {data.period || 14}</div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* MACD indicator */}
        {nodeType === 'macd' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">
              {data.fastPeriod || 12}/{data.slowPeriod || 26}/{data.signalPeriod || 9}
            </div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Bollinger Bands */}
        {nodeType === 'bollinger' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">
              Period: {data.period || 20}, σ: {data.stdDev || 2}
            </div>
            <PreviewDisplay preview={preview} color={typeDef.color} />
          </div>
        )}
        
        {/* Output node - show computed output value (always scalar) */}
        {nodeType === 'output' && (
          <div className="text-xs">
            <div className="text-gray-400 mb-1">{data.description || 'Position delta'}</div>
            <div className="text-gray-500 mb-1">input →</div>
            <PreviewDisplay 
              preview={preview} 
              color="#22c55e" 
              scalarLabel="shares"
            />
          </div>
        )}
      </div>
      
      {/* Input handles - positioned relative to body content */}
      {/* For concat, dynamically generate inputs based on numInputs */}
      {nodeType === 'concat' ? (
        Array.from({ length: data.numInputs || 2 }, (_, i) => {
          const bodyOffset = 36 + 16 + (i * 26);
          return (
            <Handle
              key={`input-input_${i}`}
              type="target"
              position={Position.Left}
              id={`input_${i}`}
              style={{
                top: bodyOffset,
                background: '#64748b',
                width: 12,
                height: 12,
                border: '2px solid #1e293b',
              }}
              title={`input_${i}`}
            />
          );
        })
      ) : (
        typeDef.inputs.map((input, i) => {
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
        })
      )}
      
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

export const RangeNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="range" />
));

export const AgentStateNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="agent_state" />
));

export const AgentEquityCurveNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="agent_equity_curve" />
));

export const CustomStateNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="custom_state" />
));

export const SignNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="sign" />
));

export const SinNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="sin" />
));

export const CosNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="cos" />
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

export const TransposeNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="transpose" />
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

export const VarianceNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="variance" />
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

export const ShiftNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="shift" />
));

export const ShiftDiffNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="shift_diff" />
));

export const Conv1dCustomNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="conv1d_custom" />
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
  // Data Sources
  signal: SignalNode,
  constant: ConstantNode,
  variable: VariableNode,
  range: RangeNode,
  agent_state: AgentStateNode,
  agent_equity_curve: AgentEquityCurveNode,
  custom_state: CustomStateNode,
  // 1-D Transformations
  slice: SliceNode,
  sign: SignNode,
  sin: SinNode,
  cos: CosNode,
  add: AddNode,
  subtract: SubtractNode,
  multiply: MultiplyNode,
  divide: DivideNode,
  normalize: NormalizeNode,
  clip: ClipNode,
  rolling_mean: RollingMeanNode,
  rolling_std: RollingStdNode,
  shift: ShiftNode,
  shift_diff: ShiftDiffNode,
  conv1d_custom: Conv1dCustomNode,
  rsi: RsiNode,
  macd: MacdNode,
  bollinger: BollingerNode,
  // Aggregation
  sum: SumNode,
  mean: MeanNode,
  std: StdNode,
  variance: VarianceNode,
  min: MinNode,
  max: MaxNode,
  // Multi-dimension Transforms
  concat: ConcatNode,
  transpose: TransposeNode,
  matmul: MatmulNode,
  // ML Layers
  linear: LinearNode,
  relu: ReluNode,
  tanh: TanhNode,
  sigmoid: SigmoidNode,
  softmax: SoftmaxNode,
  lstm: LstmNode,
  conv1d: Conv1dNode,
  // Output
  output: OutputNode,
};
