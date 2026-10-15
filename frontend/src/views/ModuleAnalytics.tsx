import { FormEvent, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  FederatedTrainResponse,
  Module,
  ModuleModelRunItem,
  ModulePredictResponse,
  ModulePredictionHistoryItem,
  listFederatedRuns,
  listModuleModels,
  listModulePredictions,
  predictModuleRisk,
  promoteModuleModel,
  trainFederatedModel,
  trainModuleModel
} from "../api";
import { useRevealSections } from "../hooks/useRevealSections";

export function ModuleAnalytics({ module, title }: { module: Module; title: string }) {
  useRevealSections();

  const [datasetFile, setDatasetFile] = useState<File | null>(null);
  const [targetColumn, setTargetColumn] = useState("risk_score");
  const [trainResult, setTrainResult] = useState<{ model_version: number; rows_trained: number; metrics: Record<string, number>; governance_synced: boolean; governance_status?: string | null; governance_error?: string | null } | null>(null);
  const [models, setModels] = useState<ModuleModelRunItem[]>([]);
  const [history, setHistory] = useState<ModulePredictionHistoryItem[]>([]);
  const [predictionRegion, setPredictionRegion] = useState("East Africa");
  const [features, setFeatures] = useState<Record<string, number>>({});
  const [prediction, setPrediction] = useState<ModulePredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [fedDatasetFile, setFedDatasetFile] = useState<File | null>(null);
  const [fedTargetColumn, setFedTargetColumn] = useState("risk_score");
  const [fedNumClients, setFedNumClients] = useState(3);
  const [fedRounds, setFedRounds] = useState(10);
  const [fedRuns, setFedRuns] = useState<FederatedTrainResponse[]>([]);
  const [fedLoading, setFedLoading] = useState(false);
  const [fedError, setFedError] = useState<string | null>(null);

  const activeModel = useMemo(() => models.find((m) => m.is_active) ?? null, [models]);

  const refreshData = async () => {
    const [modelsData, historyData] = await Promise.all([
      listModuleModels(module, 50),
      listModulePredictions(module, 20)
    ]);
    setModels(modelsData);
    setHistory(historyData);
  };

  const refreshFederatedRuns = async () => {
    setFedRuns(await listFederatedRuns(module, 10));
  };

  useEffect(() => {
    refreshData().catch((err) => setError(err instanceof Error ? err.message : "Failed to load data"));
    refreshFederatedRuns().catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [module]);

  useEffect(() => {
    if (!activeModel) {
      return;
    }
    setFeatures((prev) => {
      const next: Record<string, number> = {};
      for (const column of activeModel.feature_columns) {
        next[column] = prev[column] ?? 0.5;
      }
      return next;
    });
  }, [activeModel]);

  const onTrain = async (event: FormEvent) => {
    event.preventDefault();
    if (!datasetFile) {
      setError("Please choose a CSV file before training.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await trainModuleModel(module, datasetFile, targetColumn);
      setTrainResult(result);
      await refreshData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Training failed");
    } finally {
      setLoading(false);
    }
  };

  const onPromote = async (modelRunId: number) => {
    setLoading(true);
    setError(null);
    try {
      await promoteModuleModel(module, modelRunId);
      await refreshData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Model promotion failed");
    } finally {
      setLoading(false);
    }
  };

  const onPredict = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await predictModuleRisk(module, {
        region: predictionRegion,
        features,
        model_run_id: activeModel?.model_run_id
      });
      setPrediction(result);
      await refreshData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const onFederatedTrain = async (event: FormEvent) => {
    event.preventDefault();
    if (!fedDatasetFile) {
      setFedError("Please choose a CSV file before running federated training.");
      return;
    }
    setFedLoading(true);
    setFedError(null);
    try {
      await trainFederatedModel(module, fedDatasetFile, fedTargetColumn, fedNumClients, fedRounds);
      await refreshFederatedRuns();
    } catch (err) {
      setFedError(err instanceof Error ? err.message : "Federated training failed");
    } finally {
      setFedLoading(false);
    }
  };

  const latestFederatedRun = fedRuns[0];
  const federatedChartData = latestFederatedRun
    ? ["r2", "rmse", "mae"].map((metric) => ({
        metric: metric.toUpperCase(),
        federated: latestFederatedRun.federated_metrics[metric],
        centralized: latestFederatedRun.centralized_metrics[metric]
      }))
    : [];

  const contributionChartData = prediction
    ? Object.entries(prediction.explanation.contributions).map(([feature, value]) => ({ feature, value }))
    : [];

  return (
    <>
      <section className="card reveal-section">
        <h2>{title}: 1) Dataset Upload &amp; Training</h2>
        <form className="grid-2" onSubmit={onTrain}>
          <label>
            Dataset CSV
            <input type="file" accept=".csv" onChange={(e) => setDatasetFile(e.target.files?.[0] ?? null)} />
          </label>
          <label>
            Target Column
            <input value={targetColumn} onChange={(e) => setTargetColumn(e.target.value)} />
          </label>
          <button type="submit" disabled={loading} className="span-2">
            {loading ? "Training..." : `Train New ${title} Model`}
          </button>
        </form>
        {trainResult ? (
          <div className="hint-stack">
            <p className="hint">
              Trained v{trainResult.model_version} on {trainResult.rows_trained} rows | R2 {trainResult.metrics.r2}
            </p>
            <p className={`status-pill ${trainResult.governance_synced ? "status-pending" : "status-rejected"}`}>
              Governance {trainResult.governance_synced ? `synced: ${trainResult.governance_status}` : `sync issue: ${trainResult.governance_error}`}
            </p>
          </div>
        ) : null}
      </section>

      <section className="card reveal-section">
        <h2>2) Model Versions &amp; Active Promotion</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Version</th>
                <th>Run ID</th>
                <th>Rows</th>
                <th>R2</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => (
                <tr key={model.model_run_id}>
                  <td>v{model.model_version}</td>
                  <td>{model.model_run_id}</td>
                  <td>{model.rows_trained}</td>
                  <td>{model.metrics.r2 ?? "-"}</td>
                  <td>{model.is_active ? "Active" : "Inactive"}</td>
                  <td>
                    <button disabled={loading || model.is_active} onClick={() => onPromote(model.model_run_id)}>
                      Promote
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card reveal-section">
        <h2>3) Prediction</h2>
        <p className="hint">Active model: {activeModel ? `v${activeModel.model_version}` : "No active model"}</p>
        {activeModel ? (
          <form className="grid-2" onSubmit={onPredict}>
            <label>
              Region
              <input value={predictionRegion} onChange={(e) => setPredictionRegion(e.target.value)} />
            </label>
            {activeModel.feature_columns.map((column) => (
              <label key={column}>
                {column}
                <input
                  type="number"
                  step={0.01}
                  value={features[column] ?? 0}
                  onChange={(e) =>
                    setFeatures((prev) => ({ ...prev, [column]: Number(e.target.value) }))
                  }
                />
              </label>
            ))}
            <button type="submit" disabled={loading} className="span-2">
              {loading ? "Running..." : `Predict ${title} Risk`}
            </button>
          </form>
        ) : (
          <p className="empty-state">Train a model above before running predictions.</p>
        )}
        {prediction ? (
          <>
            <p className="hint">
              Prediction #{prediction.prediction_id} | model v{prediction.model_version} | risk{" "}
              {prediction.predicted_risk.toFixed(3)}
            </p>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={contributionChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="feature" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#0D6BC8" name="SHAP contribution" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        ) : null}
      </section>

      <section className="card reveal-section">
        <h2>4) Prediction History</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Model Run</th>
                <th>Region</th>
                <th>Predicted Risk</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {history.map((row) => (
                <tr key={row.prediction_id}>
                  <td>{row.prediction_id}</td>
                  <td>{row.model_run_id}</td>
                  <td>{row.region ?? "-"}</td>
                  <td>{row.predicted_risk.toFixed(3)}</td>
                  <td>{new Date(row.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}

      <section className="card reveal-section">
        <h2>5) Federated Learning (Simulated)</h2>
        <p className="hint">
          Simulates multiple client organizations training locally on private data shards, aggregated via federated
          averaging (FedAvg), compared against a centralized baseline trained on pooled data.
        </p>
        <form className="grid-2" onSubmit={onFederatedTrain}>
          <label>
            Dataset CSV
            <input type="file" accept=".csv" onChange={(e) => setFedDatasetFile(e.target.files?.[0] ?? null)} />
          </label>
          <label>
            Target Column
            <input value={fedTargetColumn} onChange={(e) => setFedTargetColumn(e.target.value)} />
          </label>
          <label>
            Number of Clients
            <input
              type="number"
              min={2}
              max={10}
              value={fedNumClients}
              onChange={(e) => setFedNumClients(Number(e.target.value))}
            />
          </label>
          <label>
            Rounds
            <input
              type="number"
              min={1}
              max={100}
              value={fedRounds}
              onChange={(e) => setFedRounds(Number(e.target.value))}
            />
          </label>
          <button type="submit" disabled={fedLoading} className="span-2">
            {fedLoading ? "Training..." : "Run Federated Training"}
          </button>
        </form>
        {fedError ? <p className="error">{fedError}</p> : null}
        {latestFederatedRun ? (
          <>
            <p className="hint">
              {latestFederatedRun.num_clients} clients | {latestFederatedRun.rounds} rounds | sample counts:{" "}
              {latestFederatedRun.client_sample_counts.join(", ")}
            </p>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={federatedChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="federated" fill="#5A3FD6" name="Federated" />
                  <Bar dataKey="centralized" fill="#0D6BC8" name="Centralized" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        ) : (
          <p className="empty-state">No federated training runs yet.</p>
        )}
      </section>
    </>
  );
}
