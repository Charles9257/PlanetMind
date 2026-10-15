import { FormEvent, useEffect, useState } from "react";
import {
  AgentPipelineRunResponse,
  Module,
  ModuleModelRunItem,
  listAgentPipelineRuns,
  listModuleModels,
  runAgentPipeline
} from "../api";
import { useRevealSections } from "../hooks/useRevealSections";

export function MultiAgentConsole() {
  useRevealSections();

  const [module, setModule] = useState<Module>("climate");
  const [activeModel, setActiveModel] = useState<ModuleModelRunItem | null>(null);
  const [region, setRegion] = useState("Sahel Belt");
  const [features, setFeatures] = useState<Record<string, number>>({});
  const [interventionName, setInterventionName] = useState("");
  const [interventionReduction, setInterventionReduction] = useState(0.1);
  const [interventions, setInterventions] = useState<Array<{ name: string; expected_reduction: number }>>([]);
  const [result, setResult] = useState<AgentPipelineRunResponse | null>(null);
  const [runs, setRuns] = useState<AgentPipelineRunResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshRuns = () => {
    listAgentPipelineRuns(10)
      .then(setRuns)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load run history"));
  };

  useEffect(() => {
    listModuleModels(module, 50)
      .then((models) => {
        const active = models.find((m) => m.is_active) ?? null;
        setActiveModel(active);
        if (active) {
          setFeatures((prev) => {
            const next: Record<string, number> = {};
            for (const column of active.feature_columns) {
              next[column] = prev[column] ?? 0.5;
            }
            return next;
          });
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load model"));
    refreshRuns();
  }, [module]);

  const addIntervention = () => {
    if (!interventionName) {
      return;
    }
    setInterventions((prev) => [...prev, { name: interventionName, expected_reduction: interventionReduction }]);
    setInterventionName("");
  };

  const removeIntervention = (index: number) => {
    setInterventions((prev) => prev.filter((_, i) => i !== index));
  };

  const onRun = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await runAgentPipeline({ module, region, features, interventions });
      setResult(response);
      refreshRuns();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent pipeline run failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <section className="card reveal-section">
        <h2>Multi-Agent Console</h2>
        <p className="hint">
          A sequential pipeline of five cooperating agents (ingestion, prediction, explainability, simulation,
          reporting) processes each request. Every run's step-by-step trace is persisted for auditability.
        </p>

        {!activeModel ? (
          <p className="empty-state">No active model for {module}. Train one in the Analytics view first.</p>
        ) : (
          <form className="grid-2" onSubmit={onRun}>
            <label>
              Module
              <select value={module} onChange={(e) => setModule(e.target.value as Module)}>
                <option value="climate">Climate</option>
                <option value="pandemic">Pandemic</option>
              </select>
            </label>
            <label>
              Region
              <input value={region} onChange={(e) => setRegion(e.target.value)} />
            </label>
            {activeModel.feature_columns.map((column) => (
              <label key={column}>
                {column}
                <input
                  type="number"
                  step={0.01}
                  value={features[column] ?? 0}
                  onChange={(e) => setFeatures((prev) => ({ ...prev, [column]: Number(e.target.value) }))}
                />
              </label>
            ))}

            <div className="span-2">
              <p className="hint">Interventions (optional, feeds the simulation agent)</p>
              <div className="grid-2">
                <input
                  placeholder="Intervention name"
                  value={interventionName}
                  onChange={(e) => setInterventionName(e.target.value)}
                />
                <input
                  type="number"
                  min={0}
                  max={1}
                  step={0.01}
                  value={interventionReduction}
                  onChange={(e) => setInterventionReduction(Number(e.target.value))}
                />
              </div>
              <button type="button" className="secondary" onClick={addIntervention}>
                Add Intervention
              </button>
              <ul>
                {interventions.map((item, index) => (
                  <li key={`${item.name}-${index}`}>
                    {item.name} ({item.expected_reduction}){" "}
                    <button type="button" className="secondary" onClick={() => removeIntervention(index)}>
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            <button type="submit" disabled={loading} className="span-2">
              {loading ? "Running pipeline..." : "Run Agent Pipeline"}
            </button>
          </form>
        )}

        {error ? <p className="error">{error}</p> : null}
      </section>

      {result ? (
        <section className="card reveal-section">
          <h2>Execution Trace (Run #{result.agent_run_id})</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Step</th>
                  <th>Status</th>
                  <th>Duration (ms)</th>
                </tr>
              </thead>
              <tbody>
                {result.steps.map((step) => (
                  <tr key={step.name}>
                    <td>{step.name}</td>
                    <td>
                      <span className={`status-pill ${step.status === "ok" ? "status-approved" : "status-rejected"}`}>
                        {step.status}
                      </span>
                    </td>
                    <td>{step.duration_ms}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {typeof result.final_output.summary === "string" ? (
            <p className="hint">{result.final_output.summary}</p>
          ) : null}
        </section>
      ) : null}

      <section className="card reveal-section">
        <h2>Recent Pipeline Runs</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Module</th>
                <th>Region</th>
                <th>Status</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.agent_run_id}>
                  <td>{run.agent_run_id}</td>
                  <td>{run.module}</td>
                  <td>{run.region ?? "-"}</td>
                  <td>{run.status}</td>
                  <td>{new Date(run.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
