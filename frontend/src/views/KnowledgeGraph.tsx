import { useEffect, useMemo, useState } from "react";
import { KnowledgeGraphResponse, getKnowledgeGraph } from "../api";
import { useRevealSections } from "../hooks/useRevealSections";

const CANVAS_SIZE = 640;
const CENTER = CANVAS_SIZE / 2;

const TYPE_RADIUS: Record<string, number> = {
  Module: 60,
  ModelRun: 150,
  Prediction: 230,
  Region: 300
};
const DEFAULT_RADIUS = 260;

const TYPE_COLORS: Record<string, string> = {
  Module: "#0D6BC8",
  ModelRun: "#5A3FD6",
  Prediction: "#CD6B11",
  Region: "#1E9E5A"
};
const DEFAULT_COLOR = "#666666";

export function layoutNodes(nodes: KnowledgeGraphResponse["nodes"]): Record<string, { x: number; y: number }> {
  const byType = new Map<string, KnowledgeGraphResponse["nodes"]>();
  for (const node of nodes) {
    const list = byType.get(node.type) ?? [];
    list.push(node);
    byType.set(node.type, list);
  }

  const positions: Record<string, { x: number; y: number }> = {};
  for (const [type, list] of byType.entries()) {
    const radius = TYPE_RADIUS[type] ?? DEFAULT_RADIUS;
    list.forEach((node, index) => {
      const angle = (2 * Math.PI * index) / list.length - Math.PI / 2;
      positions[node.id] = {
        x: CENTER + radius * Math.cos(angle),
        y: CENTER + radius * Math.sin(angle)
      };
    });
  }
  return positions;
}

export function KnowledgeGraph() {
  useRevealSections();

  const [graph, setGraph] = useState<KnowledgeGraphResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = () => {
    setLoading(true);
    setError(null);
    getKnowledgeGraph(100)
      .then(setGraph)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load knowledge graph"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
  }, []);

  const positions = useMemo(() => (graph ? layoutNodes(graph.nodes) : {}), [graph]);
  const presentTypes = useMemo(
    () => Array.from(new Set((graph?.nodes ?? []).map((node) => node.type))),
    [graph]
  );

  return (
    <section className="card reveal-section">
      <h2>Knowledge Graph</h2>
      <p className="hint">
        Modules, model runs, predictions, and regions captured from the platform's own data, rendered as a
        relationship graph. Refresh after training or predicting to see the graph grow.
      </p>
      <button type="button" onClick={refresh} disabled={loading}>
        {loading ? "Loading..." : "Refresh Graph"}
      </button>

      {error ? <p className="error">{error}</p> : null}

      <div className="legend">
        {presentTypes.map((type) => (
          <span key={type} className="legend-item">
            <span className="legend-swatch" style={{ background: TYPE_COLORS[type] ?? DEFAULT_COLOR }} />
            {type}
          </span>
        ))}
      </div>

      {graph && graph.nodes.length > 0 ? (
        <div className="chart-wrap">
          <svg viewBox={`0 0 ${CANVAS_SIZE} ${CANVAS_SIZE}`} width="100%" role="img" aria-label="Knowledge graph">
            {graph.edges.map((edge, index) => {
              const source = positions[edge.source];
              const target = positions[edge.target];
              if (!source || !target) {
                return null;
              }
              return (
                <line
                  key={`${edge.source}-${edge.target}-${index}`}
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke="#c7c7c7"
                  strokeWidth={1}
                />
              );
            })}
            {graph.nodes.map((node) => {
              const position = positions[node.id];
              if (!position) {
                return null;
              }
              return (
                <g key={node.id}>
                  <circle cx={position.x} cy={position.y} r={8} fill={TYPE_COLORS[node.type] ?? DEFAULT_COLOR} />
                  <text x={position.x + 10} y={position.y + 4} fontSize={10} fill="currentColor">
                    {node.label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      ) : (
        <p className="empty-state">No graph data yet. Train a model and run a prediction first.</p>
      )}
    </section>
  );
}
