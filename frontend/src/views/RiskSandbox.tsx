import { FormEvent, useState } from "react";
import { Domain, PredictionResponse, SimulationResponse, predictRisk, simulateRisk } from "../api";
import { useRevealSections } from "../hooks/useRevealSections";

const defaultSignalsByDomain: Record<Domain, Array<{ name: string; value: number }>> = {
  climate: [
    { name: "temperature_anomaly", value: 0.6 },
    { name: "rainfall_deficit", value: 0.5 },
    { name: "soil_moisture_drop", value: 0.4 },
    { name: "wildfire_index", value: 0.2 }
  ],
  health: [
    { name: "new_cases_growth", value: 0.4 },
    { name: "hospital_occupancy", value: 0.5 },
    { name: "vaccination_gap", value: 0.3 },
    { name: "mobility_spike", value: 0.2 }
  ],
  cyber: [
    { name: "malware_activity", value: 0.5 },
    { name: "phishing_rate", value: 0.4 },
    { name: "unpatched_assets", value: 0.3 },
    { name: "critical_alerts", value: 0.2 }
  ],
  economic: [
    { name: "inflation_pressure", value: 0.4 },
    { name: "unemployment_rise", value: 0.3 },
    { name: "supply_chain_delay", value: 0.3 },
    { name: "currency_volatility", value: 0.2 }
  ]
};

export function RiskSandbox() {
  useRevealSections();

  const [domain, setDomain] = useState<Domain>("climate");
  const [region, setRegion] = useState("Global");
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [simulation, setSimulation] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onPredict = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSimulation(null);
    try {
      const result = await predictRisk(domain, region, defaultSignalsByDomain[domain]);
      setPrediction(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const onSimulate = async () => {
    if (!prediction) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await simulateRisk(prediction.score, [
        { name: "early-warning-system", expected_reduction: 0.1 },
        { name: "targeted-response-fund", expected_reduction: 0.15 }
      ]);
      setSimulation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <form className="card" onSubmit={onPredict}>
        <h2>Risk Prediction Sandbox</h2>
        <label>
          Domain
          <select value={domain} onChange={(e) => setDomain(e.target.value as Domain)}>
            <option value="climate">Climate</option>
            <option value="health">Health</option>
            <option value="cyber">Cyber</option>
            <option value="economic">Economic</option>
          </select>
        </label>
        <label>
          Region
          <input value={region} onChange={(e) => setRegion(e.target.value)} />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Processing..." : "Run Prediction"}
        </button>
      </form>

      {error ? <p className="error">{error}</p> : null}

      {prediction ? (
        <section className="card reveal-section">
          <h2>Prediction Result</h2>
          <p>
            <strong>Severity:</strong> {prediction.severity} | <strong>Score:</strong> {prediction.score.toFixed(2)}
          </p>
          <p>{prediction.explanation}</p>
          <button onClick={onSimulate} disabled={loading}>
            Run Intervention Simulation
          </button>
        </section>
      ) : null}

      {simulation ? (
        <section className="card reveal-section">
          <h2>Simulation Result</h2>
          <p>{simulation.summary}</p>
          <p>
            Baseline: {simulation.baseline_score.toFixed(2)} | Projected: {simulation.projected_score.toFixed(2)} |
            Reduction: {simulation.net_reduction.toFixed(2)}
          </p>
        </section>
      ) : null}
    </>
  );
}
