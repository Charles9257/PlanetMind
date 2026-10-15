import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Module, ModulePredictionHistoryItem, listModulePredictions } from "../api";
import { useRevealSections } from "../hooks/useRevealSections";

export function Explainability() {
  useRevealSections();

  const [module, setModule] = useState<Module>("climate");
  const [history, setHistory] = useState<ModulePredictionHistoryItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listModulePredictions(module, 20)
      .then((rows) => {
        const withExplanation = rows.filter((row) => row.explanation);
        setHistory(withExplanation);
        setSelectedId(withExplanation[0]?.prediction_id ?? null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load predictions"));
  }, [module]);

  const selected = useMemo(
    () => history.find((row) => row.prediction_id === selectedId) ?? null,
    [history, selectedId]
  );

  const chartData = selected?.explanation
    ? Object.entries(selected.explanation.contributions).map(([feature, value]) => ({ feature, value }))
    : [];

  return (
    <section className="card reveal-section">
      <h2>Explainable AI</h2>
      <p className="hint">
        Every prediction is explained with SHAP (SHapley Additive exPlanations) values computed against the trained
        RandomForest model, showing how much each feature pushed the prediction above or below the model's base
        value.
      </p>

      <label>
        Module
        <select value={module} onChange={(e) => setModule(e.target.value as Module)}>
          <option value="climate">Climate</option>
          <option value="pandemic">Pandemic</option>
        </select>
      </label>

      {error ? <p className="error">{error}</p> : null}

      {history.length === 0 ? (
        <p className="empty-state">No explained predictions yet for this module. Run a prediction first.</p>
      ) : (
        <>
          <label>
            Prediction
            <select value={selectedId ?? ""} onChange={(e) => setSelectedId(Number(e.target.value))}>
              {history.map((row) => (
                <option key={row.prediction_id} value={row.prediction_id}>
                  #{row.prediction_id} - {row.region ?? "unknown region"} - risk {row.predicted_risk.toFixed(3)}
                </option>
              ))}
            </select>
          </label>

          {selected?.explanation ? (
            <>
              <p className="hint">
                Base value: {selected.explanation.base_value.toFixed(3)} | Predicted risk:{" "}
                {selected.predicted_risk.toFixed(3)}
              </p>
              <div className="chart-wrap">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={chartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="feature" width={140} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#0D6BC8" name="SHAP contribution" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : null}
        </>
      )}
    </section>
  );
}
