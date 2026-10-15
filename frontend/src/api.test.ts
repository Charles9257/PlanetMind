import { afterEach, describe, expect, it, vi } from "vitest";
import { getKnowledgeGraph, predictModuleRisk, predictRisk } from "./api";

function mockFetchOnce(body: unknown, ok = true, status = 200) {
  const response = {
    ok,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body))
  } as Response;
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("predictRisk posts to the risk predict endpoint and parses the response", async () => {
    mockFetchOnce({
      domain: "climate",
      region: "East Africa",
      score: 0.62,
      severity: "high",
      explanation: "Climate risk is high",
      top_contributors: { rainfall_deficit: 0.3 }
    });

    const result = await predictRisk("climate", "East Africa", [{ name: "rainfall_deficit", value: 0.6 }]);

    expect(result.domain).toBe("climate");
    expect(result.score).toBeCloseTo(0.62);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/risk/predict"),
      expect.objectContaining({ method: "POST" })
    );
  });

  it("predictModuleRisk hits the module-specific predict endpoint", async () => {
    mockFetchOnce({
      module: "pandemic",
      prediction_id: 1,
      model_run_id: 2,
      model_version: 1,
      region: "Southeast Asia",
      predicted_risk: 0.41,
      explanation: { base_value: 0.3, contributions: { new_cases_growth: 0.11 } },
      created_at: new Date(0).toISOString()
    });

    const result = await predictModuleRisk("pandemic", { region: "Southeast Asia", features: { new_cases_growth: 0.5 } });

    expect(result.module).toBe("pandemic");
    expect(result.explanation.contributions.new_cases_growth).toBeCloseTo(0.11);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/pandemic/predict"), expect.anything());
  });

  it("throws a descriptive error when a request fails", async () => {
    mockFetchOnce({ detail: "boom" }, false, 400);
    await expect(predictRisk("climate", "Global", [{ name: "x", value: 0.1 }])).rejects.toThrow(/400/);
  });

  it("getKnowledgeGraph parses nodes and edges", async () => {
    mockFetchOnce({
      nodes: [{ id: "module:climate", label: "Climate", type: "Module" }],
      edges: []
    });

    const graph = await getKnowledgeGraph();
    expect(graph.nodes).toHaveLength(1);
    expect(graph.nodes[0].type).toBe("Module");
  });
});
