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
type PreviewData =
  | { type: 'tensor'; values: number[] }
  | { type: 'scalar'; value: number }
  | { type: 'scalars'; values: number[] }   // 2-3 scalars for multi-output display
  | { type: 'matrix'; values: number[][] }; // 2D for heatmap

// Shape type
type ShapeDim = number | 'L';
type Shape = [ShapeDim, ShapeDim];

// Format shape for display
function formatShape(shape: Shape | null): string {
  if (!shape) return '(?, ?)';
  const [rows, cols] = shape;
  return `(${rows}, ${cols})`;
}

// Line Sparkline component for visualizing tensor/1D data
function LineSparkline({ values, color = '#22c55e', width = 130, height = 28, showLabels = true }: { 
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

// Bar/Column Sparkline component - positive values use node color, negative values are red
function BarSparkline({ values, color = '#22c55e', width = 130, height = 28 }: { 
  values: number[]; 
  color?: string;
  width?: number;
  height?: number;
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
  
  const min = Math.min(...values, 0); // Include 0 in range
  const max = Math.max(...values, 0);
  const range = max - min || 1;
  
  // Calculate zero line position
  const zeroY = height - 2 - ((0 - min) / range) * (height - 4);
  
  const barWidth = Math.max(1, (width - values.length + 1) / values.length);
  const gap = 1;
  
  return (
    <div className="bg-gray-800/50 rounded p-0.5" style={{ width: width + 4 }}>
      <svg width={width} height={height}>
        {/* Zero line */}
        <line 
          x1={0} 
          y1={zeroY} 
          x2={width} 
          y2={zeroY} 
          stroke="#4b5563" 
          strokeWidth="0.5" 
          strokeDasharray="2,2"
        />
        {values.map((v, i) => {
          const x = i * (barWidth + gap);
          const barHeight = Math.abs(((v) / range) * (height - 4));
          const isPositive = v >= 0;
          const barY = isPositive ? zeroY - barHeight : zeroY;
          const barColor = isPositive ? color : '#ef4444'; // Red for negative
          
          return (
            <rect
              key={i}
              x={x}
              y={Math.max(2, barY)}
              width={barWidth}
              height={Math.max(1, barHeight)}
              fill={barColor}
              rx={0.5}
            />
          );
        })}
      </svg>
    </div>
  );
}

// 2D Heatmap component for matrix visualization
function HeatmapDisplay({ values, color = '#ef4444', width = 140, height = 80 }: {
  values: number[][];
  color?: string;
  width?: number;
  height?: number;
}) {
  if (!values || values.length === 0 || values.every(row => row.length === 0)) {
    return (
      <div 
        className="flex items-center justify-center text-xs text-gray-500 bg-gray-800/50 rounded"
        style={{ width, height }}
      >
        No data
      </div>
    );
  }

  const flat = values.flat();
  const min = Math.min(...flat);
  const max = Math.max(...flat);
  const range = max - min || 1;

  const rows = values.length;
  const cols = Math.max(...values.map(r => r.length));

  const cellW = Math.max(2, (width - 2) / cols);
  const cellH = Math.max(2, (height - 2) / rows);

  return (
    <div className="bg-gray-800/50 rounded p-1" style={{ width: width + 4, height: height + 4 }}>
      <svg width={width} height={height}>
        {values.map((row, ri) =>
          row.map((v, ci) => {
            const intensity = (v - min) / range;
            const r = parseInt(color.slice(1, 3), 16);
            const g = parseInt(color.slice(3, 5), 16);
            const b = parseInt(color.slice(5, 7), 16);
            const fill = `rgba(${r},${g},${b},${0.3 + intensity * 0.7})`;
            return (
              <rect
                key={`${ri}-${ci}`}
                x={ci * cellW}
                y={ri * cellH}
                width={cellW - 0.5}
                height={cellH - 0.5}
                fill={fill}
                stroke="#374151"
                strokeWidth={0.5}
              />
            );
          })
        )}
      </svg>
    </div>
  );
}

// Combined Sparkline - renders line or bar based on type prop
function Sparkline({ values, color = '#22c55e', width = 130, height = 28, showLabels = true, type = 'line' }: { 
  values: number[]; 
  color?: string;
  width?: number;
  height?: number;
  showLabels?: boolean;
  type?: 'line' | 'bar';
}) {
  if (type === 'bar') {
    return <BarSparkline values={values} color={color} width={width} height={height} />;
  }
  return <LineSparkline values={values} color={color} width={width} height={height} showLabels={showLabels} />;
}

// Format a scalar value for display
function formatScalarValue(v: number): string {
  if (Math.abs(v) >= 1000) return v.toFixed(0);
  if (Math.abs(v) >= 100) return v.toFixed(1);
  if (Math.abs(v) >= 1) return v.toFixed(2);
  return v.toFixed(4);
}

// Scalar value display component
function ScalarDisplay({ value, color = '#22c55e', label }: { 
  value: number; 
  color?: string;
  label?: string;
}) {
  return (
    <div className="bg-gray-800/50 rounded p-2 text-center">
      <span 
        className="text-lg font-mono"
        style={{ color }}
      >
        {formatScalarValue(value)}
      </span>
      {label && <div className="text-gray-500 text-xs mt-1">{label}</div>}
    </div>
  );
}

// Multiple scalars display: (s1, s2, ...) up to 6 values
function ScalarTupleDisplay({ values, color = '#22c55e', label }: {
  values: number[];
  color?: string;
  label?: string;
}) {
  const displayValues = values.slice(0, 6).map(v => formatScalarValue(v));
  return (
    <div className="bg-gray-800/50 rounded p-2 text-center">
      <span 
        className="text-lg font-mono"
        style={{ color }}
      >
        ({displayValues.join(', ')})
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
  scalarLabel,
  sparklineType = 'line'
}: { 
  preview?: PreviewData;
  color: string;
  width?: number;
  height?: number;
  scalarLabel?: string;
  sparklineType?: 'line' | 'bar';
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
  
  if (preview.type === 'scalars' && preview.values.length >= 1) {
    return <ScalarTupleDisplay values={preview.values} color={color} label={scalarLabel} />;
  }
  
  return <Sparkline values={preview.type === 'tensor' ? preview.values : []} color={color} width={width} height={height} type={sparklineType} />;
}

/**
 * View Output Display - meter/debugger: shows scalar, sparkline, or 2D heatmap based on input.
 */
function ViewOutputDisplay({
  preview,
  shape,
  color = '#ef4444',
  width = 140,
  height = 80
}: {
  preview?: PreviewData;
  shape?: Shape | null;
  color?: string;
  width?: number;
  height?: number;
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

  if (preview.type === 'matrix' && preview.values.length > 0) {
    return <HeatmapDisplay values={preview.values} color={color} width={width} height={height} />;
  }

  if (preview.type === 'scalar') {
    return <ScalarDisplay value={preview.value} color={color} />;
  }

  if (preview.type === 'scalars' && preview.values.length >= 1) {
    return <ScalarTupleDisplay values={preview.values} color={color} />;
  }

  const isScalarShape = shape && shape[0] === 1 && shape[1] === 1;
  const scalarValue = preview.type === 'tensor' && preview.values.length === 1
    ? preview.values[0] : null;
  if (isScalarShape && scalarValue !== null) {
    return <ScalarDisplay value={scalarValue} color={color} />;
  }

  const values = preview.type === 'tensor' ? preview.values : [];
  return <Sparkline values={values} color={color} width={width} height={height} />;
}

/**
 * Smart preview display - dynamically shows scalar, (s1,s2,s3), or sparkline based on shape and preview.
 * Use this for all 1-D transforms and signals for consistent display behavior.
 */
function SmartPreviewDisplay({ 
  preview, 
  shape,
  color, 
  width = 130, 
  height = 28,
  scalarLabel,
  sparklineType = 'line'
}: { 
  preview?: PreviewData;
  shape?: Shape | null;
  color: string;
  width?: number;
  height?: number;
  scalarLabel?: string;
  sparklineType?: 'line' | 'bar';
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
  
  // Multiple scalars (2–6): display (s1, s2, ...)
  if (preview.type === 'scalars' && preview.values.length >= 1) {
    return <ScalarTupleDisplay values={preview.values} color={color} label={scalarLabel} />;
  }
  
  // Single scalar: shape (1,1) or explicit scalar type
  const isScalarShape = shape && shape[0] === 1 && shape[1] === 1;
  const scalarValue = preview.type === 'scalar' 
    ? preview.value 
    : (preview.type === 'tensor' && preview.values.length === 1) ? preview.values[0] : null;
  
  if (isScalarShape && scalarValue !== null) {
    return <ScalarDisplay value={scalarValue} color={color} label={scalarLabel} />;
  }
  if (preview.type === 'scalar') {
    return <ScalarDisplay value={preview.value} color={color} label={scalarLabel} />;
  }
  
  // Tensor/vector: show sparkline
  const values = preview.type === 'tensor' ? preview.values : [];
  return <Sparkline values={values} color={color} width={width} height={height} type={sparklineType} />;
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
  const sparklineType = (data.sparklineType || 'line') as 'line' | 'bar';
  
  if (!typeDef) {
    return <div className="p-2 bg-gray-700 rounded">Unknown: {nodeType}</div>;
  }
  
  const borderColor = selected ? '#fff' : typeDef.color;
  // For concat, use dynamic numInputs; for others, use typeDef
  const numInputs = nodeType === 'concat' ? (data.numInputs || 2) : typeDef.inputs.length;
  const numOutputs = typeDef.outputs.length;
  const maxHandles = Math.max(numInputs, numOutputs, 1);
  
  // Calculate minimum height based on number of handles
  // Show preview for all nodes that have outputs or are sinks (output, view_output)
  const hasPreview = typeDef.outputs.length > 0 || nodeType === 'output' || nodeType === 'view_output';
  const baseBodyHeight = hasPreview ? 70 : 40;
  const handleHeight = maxHandles * 26;
  const minBodyHeight = Math.max(baseBodyHeight, handleHeight);
  
  // Don't show resizer for output nodes to avoid the white box issue
  const showResizer = selected && nodeType !== 'output' && nodeType !== 'view_output';
  
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
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} width={156} height={32} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Constant-specific: show value and preview */}
        {nodeType === 'constant' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1">Value: {data.value ?? 0}</div>
            {data.shape && data.shape.length > 1 && (
              <div className="text-gray-500 mb-1">Shape: [{data.shape.join('×')}]</div>
            )}
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} width={130} height={24} sparklineType={sparklineType} />
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
              <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} width={130} height={24} sparklineType={sparklineType} />
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
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} width={130} height={28} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Timestamp: year, month, weeknumber, day_of_week, hour, timestamp_seconds */}
        {nodeType === 'timestamp' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-0.5 text-[10px]">year | month | week | dow | hour | ts_sec</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
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
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Custom State (legacy single block) */}
        {nodeType === 'custom_state' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1 font-mono text-[10px]">
              {data.stateName || 'my_state'}
            </div>
            <div className="text-gray-600 text-[10px] mb-1">
              default: {data.defaultValue || '0'}
            </div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Sign function */}
        {nodeType === 'sign' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">sign(x): 1 if x{'>'} 0, 0 if x=0, -1 if x{'<'} 0</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Sin function */}
        {nodeType === 'sin' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">sin(x)</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Cos function */}
        {nodeType === 'cos' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">cos(x)</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Slice-specific: show window range and live preview */}
        {nodeType === 'slice' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">
              [{-(data.n || 10)} : {(data.m ?? 0) === 0 ? 'end' : -(data.m ?? 0)}]
            </div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Concat node - dynamic inputs */}
        {nodeType === 'concat' && (
          <div className="text-xs text-gray-300">
            {Array.from({ length: data.numInputs || 2 }, (_, i) => (
              <div key={i} className="text-gray-500">input_{i} →</div>
            ))}
            <div className="mb-1"></div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Binary ops: add, subtract, multiply, divide */}
        {['add', 'multiply', 'divide'].includes(nodeType) && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500">a →</div>
            <div className="text-gray-500 mb-1">b →</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        {nodeType === 'subtract' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-0.5">{data.subtractMode === 'ratio' ? '(a-b)/b' : 'a - b'}</div>
            <div className="text-gray-500">a →</div>
            <div className="text-gray-500 mb-1">b →</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        {/* Abs */}
        {nodeType === 'abs' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">|x|</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        {/* Parity Check */}
        {nodeType === 'parity_check' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-0.5">parity: 1 same, -1 opposite, 0 any zero</div>
            <div className="text-gray-500 mb-1">aligned_sign: 1 both pos, -1 both neg, 0 else</div>
            <div className="text-gray-500">a →</div>
            <div className="text-gray-500 mb-1">b →</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Flip - parity: -1↔1, 0→0; boolean: 0↔1 */}
        {nodeType === 'flip' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">
              {data.flipMode === 'boolean' ? '0↔1' : '-1↔1, 0→0'}
            </div>
            <div className="text-gray-500 mb-1">input →</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Parity Split - positive→first output, negative→second output */}
        {nodeType === 'parity_split' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-0.5">pos: value if &gt; 0 else 0</div>
            <div className="text-gray-500 mb-1">neg: value if &lt; 0 else 0</div>
            <div className="text-gray-500 mb-1">input →</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Compare - a op b → 1 or 0 */}
        {nodeType === 'compare' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">
              a {data.compareOp === 'gt' ? '>' : data.compareOp === 'lt' ? '<' : data.compareOp === 'gte' ? '≥' : data.compareOp === 'lte' ? '≤' : data.compareOp === 'eq' ? '=' : '≠'} b → 1 or 0
            </div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Crossover - detects when fast crosses slow */}
        {nodeType === 'crossover' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-0.5">cross_above: fast↗slow</div>
            <div className="text-gray-500 mb-1">cross_below: fast↘slow</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Threshold - input vs threshold */}
        {nodeType === 'threshold' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">
              {data.mode === 'below' ? `input < ${data.threshold ?? 0}` : `input > ${data.threshold ?? 0}`} → 1 or 0
            </div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* EMA - exponential moving average */}
        {nodeType === 'ema' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">Span: {data.span ?? 10}</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Transpose */}
        {nodeType === 'transpose' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">Swaps (R, C) → (C, R)</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* MatMul - outputs scalar (dot product result) */}
        {nodeType === 'matmul' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500">a →</div>
            <div className="text-gray-500 mb-1">b →</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} scalarLabel="result" />
          </div>
        )}
        
        {/* Aggregation ops: mean, sum, min, max - output scalar */}
        {['mean', 'sum', 'min', 'max'].includes(nodeType) && (
          <div className="text-xs text-gray-300">
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} scalarLabel={nodeType} />
          </div>
        )}
        
        {/* Std Dev - show population vs sample */}
        {nodeType === 'std' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">
              {data.ddof === 1 ? 'Sample' : 'Population'}
            </div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} scalarLabel="std dev" />
          </div>
        )}
        
        {/* Variance - show population vs sample */}
        {nodeType === 'variance' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">
              {data.ddof === 1 ? 'Sample' : 'Population'}
            </div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} scalarLabel="variance" />
          </div>
        )}
        
        {/* Normalize */}
        {nodeType === 'normalize' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">Z-score normalization</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Clip-specific: show range */}
        {nodeType === 'clip' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">[{data.min ?? -1}, {data.max ?? 1}]</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Round: decimals, method */}
        {nodeType === 'round' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">
              {data.roundMethod === 'up' ? 'ceil' : data.roundMethod === 'down' ? 'floor' : 'round'} to {data.decimals ?? 0} decimals
            </div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Rolling ops: show window */}
        {(nodeType === 'rolling_mean' || nodeType === 'rolling_std') && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">Window: {data.window || 10}</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
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
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Custom State _t (green input) */}
        {(nodeType === 'custom_state_t') && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1 font-mono text-[10px]">
              {data.stateName || 'my_state'}_t
            </div>
            <div className="text-gray-600 text-[10px] mb-1">Current value (input)</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        {/* Custom State _(t+1) (red output) */}
        {nodeType === 'custom_state_t1' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1 font-mono text-[10px]">
              {data.stateName || 'my_state'}_(t+1)
            </div>
            <div className="text-gray-600 text-[10px] mb-1">New value (output) → updates state</div>
            <div className="text-gray-500">new_value →</div>
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
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Conv1D Custom: kernel from input, padding option */}
        {nodeType === 'conv1d_custom' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500 text-[10px]">
              kernel: from input
            </div>
            <div className="mb-1 text-gray-600 text-[10px]">
              {data.padding === 'same' ? 'Same (preserve len)' : 'Valid (shorter)'}
            </div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Linear layer: show dimensions */}
        {nodeType === 'linear' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">{data.inFeatures || 10} → {data.outFeatures || 1}</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Activation functions */}
        {['relu', 'tanh', 'sigmoid', 'softmax'].includes(nodeType) && (
          <div className="text-xs text-gray-300">
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* LSTM: show config */}
        {nodeType === 'lstm' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">Hidden: {data.hiddenSize || 32}</div>
            <div className="text-gray-500">output →</div>
            <div className="text-gray-500">hidden →</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Conv1D: show config */}
        {nodeType === 'conv1d' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500">{data.inChannels || 1} → {data.outChannels || 16}</div>
            <div className="text-gray-500 mb-1">kernel: {data.kernelSize || 3}</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* RSI indicator */}
        {nodeType === 'rsi' && (
          <div className="text-xs text-gray-300">
            <div className="mb-1 text-gray-500">Period: {data.period || 14}</div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* MACD indicator */}
        {nodeType === 'macd' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">
              {data.fastPeriod || 12}/{data.slowPeriod || 26}/{data.signalPeriod || 9}
            </div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Bollinger Bands */}
        {nodeType === 'bollinger' && (
          <div className="text-xs text-gray-300">
            <div className="text-gray-500 mb-1">
              Period: {data.period || 20}, σ: {data.stdDev || 2}
            </div>
            <SmartPreviewDisplay preview={preview} shape={shape} color={typeDef.color} sparklineType={sparklineType} />
          </div>
        )}
        
        {/* Output node - show computed output value (always scalar) */}
        {nodeType === 'output' && (
          <div className="text-xs">
            <div className="text-gray-400 mb-1">{data.description || 'Position delta'}</div>
            <div className="text-gray-500 mb-1">input →</div>
            <SmartPreviewDisplay 
              preview={preview} 
              shape={shape}
              color="#22c55e" 
              scalarLabel="shares"
            />
          </div>
        )}
        
        {/* View Output - meter/debugger: sparkline, scalar, or 2D heatmap */}
        {nodeType === 'view_output' && (
          <div className="text-xs">
            <div className="text-gray-400 mb-1">{data.description || 'Meter / debugger'}</div>
            <div className="text-gray-500 mb-1">input →</div>
            <ViewOutputDisplay preview={preview} shape={shape} color={typeDef.color} width={140} height={80} />
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

export const TimestampNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="timestamp" />
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

export const AbsNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="abs" />
));

export const ParityCheckNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="parity_check" />
));

export const FlipNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="flip" />
));

export const ParitySplitNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="parity_split" />
));

export const CompareNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="compare" />
));

export const CrossoverNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="crossover" />
));

export const ThresholdNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="threshold" />
));

export const EmaNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="ema" />
));

export const CustomStateTNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="custom_state_t" />
));

export const CustomStateT1Node = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="custom_state_t1" />
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

export const RoundNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="round" />
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

export const ViewOutputNode = memo((props: NodeProps) => (
  <BaseNode {...props} nodeType="view_output" />
));

// Export all node types as a map for ReactFlow
export const nodeTypes = {
  // Data Sources
  signal: SignalNode,
  constant: ConstantNode,
  variable: VariableNode,
  range: RangeNode,
  timestamp: TimestampNode,
  agent_state: AgentStateNode,
  agent_equity_curve: AgentEquityCurveNode,
  custom_state: CustomStateNode,
  custom_state_t: CustomStateTNode,
  custom_state_t1: CustomStateT1Node,
  // 1-D Transformations
  slice: SliceNode,
  sign: SignNode,
  sin: SinNode,
  cos: CosNode,
  add: AddNode,
  subtract: SubtractNode,
  abs: AbsNode,
  parity_check: ParityCheckNode,
  flip: FlipNode,
  parity_split: ParitySplitNode,
  compare: CompareNode,
  crossover: CrossoverNode,
  threshold: ThresholdNode,
  ema: EmaNode,
  multiply: MultiplyNode,
  divide: DivideNode,
  normalize: NormalizeNode,
  clip: ClipNode,
  round: RoundNode,
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
  view_output: ViewOutputNode,
};
