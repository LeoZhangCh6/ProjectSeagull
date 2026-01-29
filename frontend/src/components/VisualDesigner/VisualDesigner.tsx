/**
 * Visual Agent Designer - Main Component
 * 
 * A node-based visual programming environment for designing trading agents.
 * Uses ReactFlow for the canvas and node connections.
 */

import { useCallback, useState, useRef, useEffect } from 'react';
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
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { X, Save, Play, Code, FolderOpen, Plus, Trash2, Upload, Download } from 'lucide-react';
import { nodeTypes } from './CustomNodes';
import { getNodeTypesByCategory, NODE_TYPES, CATEGORY_COLORS } from './nodeTypes';
import { visualDesignerApi, signalsApi } from '../../api/client';
import type { Signal, VisualDesign, VisualDesignGraph, CodeGenerationResult, ValidationResult } from '../../types';

interface VisualDesignerProps {
  isOpen: boolean;
  onClose: () => void;
  initialDesign?: VisualDesign;
  onSave?: (design: VisualDesign) => void;
}

// Toolbox panel component
function Toolbox({ onAddNode }: { onAddNode: (type: string) => void }) {
  const categories = getNodeTypesByCategory();
  const categoryNames: Record<string, string> = {
    data: 'Data Sources',
    operation: 'Operations',
    indicator: 'Indicators',
    ml: 'ML Layers',
    output: 'Output',
  };
  
  return (
    <div className="w-48 bg-[var(--bg-secondary)] border-r border-[var(--border-color)] overflow-y-auto">
      <div className="p-2 text-sm font-medium border-b border-[var(--border-color)]">
        Node Toolbox
      </div>
      {Object.entries(categories).map(([category, nodes]) => (
        <div key={category} className="border-b border-[var(--border-color)]">
          <div 
            className="px-2 py-1 text-xs font-medium text-[var(--text-secondary)]"
            style={{ borderLeft: `3px solid ${CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS]}` }}
          >
            {categoryNames[category]}
          </div>
          <div className="p-1 space-y-1">
            {nodes.map(node => (
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
      ))}
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
        
        {/* Signal-specific: signal selector */}
        {nodeType === 'signal' && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Signal</label>
            <select
              value={data.signalId || ''}
              onChange={(e) => handleChange('signalId', e.target.value)}
              className="w-full text-sm"
            >
              <option value="">Select signal...</option>
              {signals.map(s => (
                <option key={s.id} value={s.id}>{s.id}</option>
              ))}
            </select>
          </div>
        )}
        
        {/* Constant-specific */}
        {nodeType === 'constant' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Value</label>
              <input
                type="number"
                value={data.value ?? 0}
                onChange={(e) => handleChange('value', parseFloat(e.target.value) || 0)}
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
        
        {/* Slice-specific */}
        {nodeType === 'slice' && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Last N elements</label>
            <input
              type="number"
              value={data.n || 10}
              onChange={(e) => handleChange('n', parseInt(e.target.value) || 10)}
              className="w-full text-sm"
              min={1}
            />
          </div>
        )}
        
        {/* Clip-specific */}
        {nodeType === 'clip' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Min</label>
              <input
                type="number"
                value={data.min ?? -1}
                onChange={(e) => handleChange('min', parseFloat(e.target.value))}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Max</label>
              <input
                type="number"
                value={data.max ?? 1}
                onChange={(e) => handleChange('max', parseFloat(e.target.value))}
                className="w-full text-sm"
              />
            </div>
          </>
        )}
        
        {/* Rolling ops */}
        {(nodeType === 'rolling_mean' || nodeType === 'rolling_std') && (
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Window</label>
            <input
              type="number"
              value={data.window || 10}
              onChange={(e) => handleChange('window', parseInt(e.target.value) || 10)}
              className="w-full text-sm"
              min={1}
            />
          </div>
        )}
        
        {/* Linear layer */}
        {nodeType === 'linear' && (
          <>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Input Features</label>
              <input
                type="number"
                value={data.inFeatures || 10}
                onChange={(e) => handleChange('inFeatures', parseInt(e.target.value) || 10)}
                className="w-full text-sm"
                min={1}
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--text-secondary)] mb-1">Output Features</label>
              <input
                type="number"
                value={data.outFeatures || 1}
                onChange={(e) => handleChange('outFeatures', parseInt(e.target.value) || 1)}
                className="w-full text-sm"
                min={1}
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
  
  // Load signals on mount
  useEffect(() => {
    signalsApi.list()
      .then(setSignals)
      .catch(console.error);
  }, []);
  
  // Node/edge change handlers
  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setNodes((nds) => applyNodeChanges(changes, nds));
  }, []);
  
  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    setEdges((eds) => applyEdgeChanges(changes, eds));
  }, []);
  
  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) => addEdge(connection, eds));
  }, []);
  
  // Node selection
  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);
  
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);
  
  // Update node data
  const handleUpdateNode = useCallback((id: string, newData: any) => {
    setNodes((nds) => 
      nds.map((node) => 
        node.id === id ? { ...node, data: newData } : node
      )
    );
    // Update selected node if it's the one being edited
    setSelectedNode((prev) => 
      prev?.id === id ? { ...prev, data: newData } : prev
    );
  }, []);
  
  // Add new node
  const handleAddNode = useCallback((type: string) => {
    const typeDef = NODE_TYPES[type as keyof typeof NODE_TYPES];
    if (!typeDef) return;
    
    const newNode: Node = {
      id: `${type}-${Date.now()}`,
      type,
      position: { x: 200 + Math.random() * 100, y: 100 + Math.random() * 100 },
      data: { ...typeDef.defaultData },
    };
    
    setNodes((nds) => [...nds, newNode]);
  }, []);
  
  // Delete selected node
  const handleDeleteSelected = useCallback(() => {
    if (!selectedNode) return;
    setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
    setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
    setSelectedNode(null);
  }, [selectedNode]);
  
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
  
  // Save design
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
      
      if (onSave) onSave(saved);
      alert('Design saved!');
    } catch (e) {
      alert(`Failed to save: ${e instanceof Error ? e.message : 'Unknown error'}`);
    }
  }, [designId, designName, nodes, edges, symbol, timespan, multiplier, onSave]);
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedNode && document.activeElement?.tagName !== 'INPUT') {
          handleDeleteSelected();
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNode, handleDeleteSelected]);
  
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
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
            snapToGrid
            snapGrid={[15, 15]}
            defaultEdgeOptions={{
              type: 'smoothstep',
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
