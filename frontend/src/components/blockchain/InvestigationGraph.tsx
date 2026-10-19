/**
 * InvestigationGraph — Cytoscape.js interactive graph visualization.
 *
 * Renders blockchain transaction and token transfer graphs.
 * Nodes represent wallets, contracts, transactions, and token contracts.
 * Edges represent observed on-chain transfers backed by evidence records.
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import cytoscape, { type Core, type EventObject } from 'cytoscape';
import type { CytoscapeGraphResponse, CytoscapeNodeData, CytoscapeEdgeData } from '@/types/blockchain';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { Maximize2, Minimize2, RotateCcw, ZoomIn, ZoomOut, Network } from 'lucide-react';
import { cn } from '@/lib/utils';

// Node colors by type
const NODE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  wallet: { bg: '#22d3ee', border: '#0e7490', text: '#0d0f14' },
  contract: { bg: '#8b5cf6', border: '#6d28d9', text: '#ffffff' },
  transaction: { bg: '#10b981', border: '#065f46', text: '#0d0f14' },
  token_contract: { bg: '#f59e0b', border: '#b45309', text: '#0d0f14' },
};

// Edge colors by type
const EDGE_COLORS: Record<string, string> = {
  sender_to_tx: '#22d3ee',
  tx_to_recipient: '#10b981',
  wallet_to_token_transfer: '#f59e0b',
  contract_to_event: '#8b5cf6',
};

interface InvestigationGraphProps {
  graph: CytoscapeGraphResponse;
  className?: string;
  onNodeClick?: (nodeData: CytoscapeNodeData) => void;
  onEdgeClick?: (edgeData: CytoscapeEdgeData) => void;
}

export function InvestigationGraph({
  graph,
  className,
  onNodeClick,
  onEdgeClick,
}: InvestigationGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<CytoscapeNodeData | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const initGraph = useCallback(() => {
    if (!containerRef.current) return;

    // Destroy existing instance
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const elements = [
      ...graph.nodes.map((n) => ({
        group: 'nodes' as const,
        data: {
          ...n.data,
          color: NODE_COLORS[n.data.node_type]?.bg ?? '#64748b',
          borderColor: NODE_COLORS[n.data.node_type]?.border ?? '#475569',
          textColor: NODE_COLORS[n.data.node_type]?.text ?? '#ffffff',
        },
      })),
      ...graph.edges.map((e) => ({
        group: 'edges' as const,
        data: {
          ...e.data,
          color: EDGE_COLORS[e.data.edge_type] ?? '#64748b',
        },
      })),
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'border-color': 'data(borderColor)',
            'border-width': 2,
            label: 'data(label)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'font-size': '10px',
            color: '#94a3b8',
            'text-margin-y': 6,
            'text-wrap': 'ellipsis',
            'text-max-width': '100px',
            width: 40,
            height: 40,
          },
        },
        {
          selector: 'node[node_type = "transaction"]',
          style: {
            shape: 'diamond',
            width: 30,
            height: 30,
          },
        },
        {
          selector: 'node[node_type = "token_contract"]',
          style: {
            shape: 'hexagon',
            width: 35,
            height: 35,
          },
        },
        {
          selector: 'node[node_type = "contract"]',
          style: {
            shape: 'rectangle',
            width: 36,
            height: 36,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#22d3ee',
            'background-color': '#38bdf8',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': 'data(color)',
            'target-arrow-color': 'data(color)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(label)',
            'font-size': '8px',
            color: '#64748b',
            'text-rotation': 'autorotate',
            'text-margin-y': -8,
          },
        },
        {
          selector: 'edge:selected',
          style: {
            width: 3,
            'line-color': '#22d3ee',
            'target-arrow-color': '#22d3ee',
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: true,
        animationDuration: 600,
        padding: 40,
        nodeRepulsion: () => 8000,
        idealEdgeLength: () => 120,
        gravity: 0.25,
      },
      minZoom: 0.2,
      maxZoom: 4,
      wheelSensitivity: 0.3,
    });

    // Event handlers
    cy.on('tap', 'node', (evt: EventObject) => {
      const data = evt.target.data() as CytoscapeNodeData;
      setSelectedNode(data);
      onNodeClick?.(data);
    });

    cy.on('tap', 'edge', (evt: EventObject) => {
      const data = evt.target.data() as CytoscapeEdgeData;
      onEdgeClick?.(data);
    });

    cy.on('tap', (evt: EventObject) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;
  }, [graph, onNodeClick, onEdgeClick]);

  useEffect(() => {
    initGraph();
    return () => {
      cyRef.current?.destroy();
    };
  }, [initGraph]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.3);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.7);
  const handleFit = () => cyRef.current?.fit(undefined, 40);

  if (graph.nodes.length === 0) {
    return (
      <Card className={className}>
        <EmptyState
          icon={<Network className="h-6 w-6" />}
          title="No graph data"
          description="Run an investigation to generate the transaction graph."
        />
      </Card>
    );
  }

  return (
    <Card className={cn('relative', isFullscreen && 'fixed inset-4 z-50', className)}>
      <CardHeader>
        <CardTitle>
          Investigation Graph
          <span className="text-text-muted font-normal ml-2 text-xs">
            {graph.meta.total_nodes} nodes · {graph.meta.total_edges} edges
          </span>
        </CardTitle>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={handleZoomIn} aria-label="Zoom in">
            <ZoomIn className="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleZoomOut} aria-label="Zoom out">
            <ZoomOut className="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleFit} aria-label="Fit view">
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsFullscreen((f) => !f)}
            aria-label={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div
          ref={containerRef}
          className={cn(
            'w-full bg-background rounded border border-border-subtle',
            isFullscreen ? 'h-[calc(100vh-10rem)]' : 'h-[420px]'
          )}
        />
        {graph.meta.max_nodes_reached && (
          <p className="text-xs text-accent-amber mt-2">
            ⚠ Node limit reached. Some elements were omitted from the graph.
          </p>
        )}
        {/* Selected node info panel */}
        {selectedNode && (
          <div className="mt-3 p-3 rounded border border-border bg-background-secondary animate-fade-in">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={selectedNode.node_type === 'wallet' ? 'info' : selectedNode.node_type === 'contract' ? 'warning' : 'success'}>
                {selectedNode.node_type}
              </Badge>
              <span className="text-sm font-mono text-text-primary">{selectedNode.label}</span>
            </div>
            {selectedNode.address && (
              <p className="text-xs text-text-muted font-mono break-all">
                Address: {selectedNode.address}
              </p>
            )}
            {selectedNode.tx_hash && (
              <p className="text-xs text-text-muted font-mono break-all">
                Tx: {selectedNode.tx_hash}
              </p>
            )}
          </div>
        )}
        {/* Legend */}
        <div className="flex flex-wrap gap-3 mt-3 text-xs text-text-muted">
          {Object.entries(NODE_COLORS).map(([type, colors]) => (
            <div key={type} className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: colors.bg, border: `1px solid ${colors.border}` }} />
              <span>{type.replace('_', ' ')}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
