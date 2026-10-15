import { describe, expect, it } from "vitest";
import { layoutNodes } from "./KnowledgeGraph";

describe("layoutNodes", () => {
  it("places every node at a finite, distinct-per-type position", () => {
    const nodes = [
      { id: "module:climate", label: "Climate", type: "Module" },
      { id: "model_run:1", label: "climate v1", type: "ModelRun" },
      { id: "model_run:2", label: "climate v2", type: "ModelRun" },
      { id: "prediction:1", label: "Prediction #1", type: "Prediction" }
    ];

    const positions = layoutNodes(nodes);

    expect(Object.keys(positions)).toHaveLength(4);
    for (const node of nodes) {
      const position = positions[node.id];
      expect(position).toBeDefined();
      expect(Number.isFinite(position.x)).toBe(true);
      expect(Number.isFinite(position.y)).toBe(true);
    }

    // The two ModelRun nodes share a ring but must not collapse onto the same point.
    const run1 = positions["model_run:1"];
    const run2 = positions["model_run:2"];
    expect(run1.x !== run2.x || run1.y !== run2.y).toBe(true);
  });

  it("returns an empty layout for an empty node list", () => {
    expect(layoutNodes([])).toEqual({});
  });
});
