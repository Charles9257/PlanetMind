import { useEffect, useState } from "react";
import { useRevealSections } from "../hooks/useRevealSections";
import { ViewKey } from "../types";

const kpiCards = [
  { label: "Prediction Workflows", value: "24/7" },
  { label: "Model Versions Tracked", value: "100+" },
  { label: "Decision Latency", value: "< 3 min" },
  { label: "Audit Coverage", value: "99.9%" }
];

function ModuleIcon({ kind }: { kind: "climate" | "risk" | "agents" | "graph" }) {
  const palette: Record<string, [string, string]> = {
    climate: ["#D8ECFF", "#0D6BC8"],
    risk: ["#FFE8D2", "#CD6B11"],
    agents: ["#E4E0FF", "#5A3FD6"],
    graph: ["#DFF6E4", "#1E9E5A"]
  };
  const [bg, stroke] = palette[kind];
  return (
    <svg viewBox="0 0 48 48" className="module-icon" aria-hidden="true">
      <rect x="4" y="6" width="40" height="36" rx="10" fill={bg} />
      <path d="M10 31C14 24 18 29 22 23C25 18 30 19 34 15" stroke={stroke} strokeWidth="3" fill="none" />
      <circle cx="34" cy="15" r="3" fill={stroke} />
    </svg>
  );
}

const modules: Array<{ kind: "climate" | "risk" | "agents" | "graph"; title: string; description: string; view: ViewKey }> = [
  {
    kind: "climate",
    title: "Climate & Pandemic Analytics",
    description:
      "Upload datasets, train versioned models, promote active versions, run predictions with SHAP explanations, and review prediction history.",
    view: "climate"
  },
  {
    kind: "risk",
    title: "Risk Sandbox",
    description:
      "Run fast scenario scoring across climate, health, cyber, and economic domains. Simulate interventions to estimate impact.",
    view: "risk"
  },
  {
    kind: "agents",
    title: "Multi-Agent Console",
    description:
      "Trigger the ingestion → prediction → explainability → simulation → reporting agent pipeline and inspect its execution trace.",
    view: "agents"
  },
  {
    kind: "graph",
    title: "Knowledge Graph",
    description: "Explore how modules, model runs, predictions, and regions connect across the platform.",
    view: "knowledge-graph"
  }
];

export function Home({ onNavigate }: { onNavigate: (view: ViewKey) => void }) {
  const [isNavCompact, setIsNavCompact] = useState(false);
  useRevealSections();

  useEffect(() => {
    const onScroll = () => setIsNavCompact(window.scrollY > 90);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const navigateSection = (sectionId: string) => {
    const target = document.getElementById(sectionId);
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <>
      <section id="overview" className="hero card reveal-section">
        <h2>Unified Planetary Risk Intelligence</h2>
        <p>
          PlanetMind is a decision-support platform for global risk teams. It combines data ingestion, model lifecycle
          management, predictive analytics, explainable AI, multi-agent orchestration, federated learning, and a
          cross-domain knowledge graph.
        </p>
        <div className="hero-actions">
          <button type="button" onClick={() => onNavigate("climate")}>Go to Climate Analytics</button>
          <button type="button" className="secondary" onClick={() => onNavigate("risk")}>Open Risk Sandbox</button>
        </div>

        <div className="kpi-grid">
          {kpiCards.map((item) => (
            <article key={item.label} className="kpi-card">
              <p>{item.label}</p>
              <strong>{item.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <section className={`home-anchor-nav card reveal-section ${isNavCompact ? "compact" : ""}`}>
        <button type="button" onClick={() => navigateSection("overview")}>Overview</button>
        <button type="button" onClick={() => navigateSection("modules")}>Modules</button>
        <button type="button" onClick={() => navigateSection("about")}>About</button>
        <button type="button" onClick={() => navigateSection("architecture")}>Architecture</button>
        <button type="button" onClick={() => navigateSection("contact")}>Contact</button>
      </section>

      <section id="modules" className="card reveal-section">
        <h2>Platform Modules</h2>
        <div className="module-grid">
          {modules.map((module) => (
            <article className="module-card" key={module.title}>
              <ModuleIcon kind={module.kind} />
              <h3>{module.title}</h3>
              <p>{module.description}</p>
              <button type="button" onClick={() => onNavigate(module.view)}>Enter Module</button>
            </article>
          ))}
        </div>
      </section>

      <section id="about" className="card reveal-section">
        <h2>About PlanetMind</h2>
        <p>
          PlanetMind is designed for strategy teams, emergency operations centers, and risk analysts who need one
          shared operating picture. The platform standardizes model governance, evidence-backed predictions, and
          transparent reporting for high-impact decisions.
        </p>
        <p>
          By combining data, intelligence, and response simulation in one place, PlanetMind helps organizations move
          from reactive reporting to proactive resilience planning.
        </p>
      </section>

      <section id="architecture" className="card reveal-section">
        <h2>Architecture</h2>
        <div className="architecture-grid">
          <article>
            <h3>Data & Ingestion</h3>
            <p>CSV and structured risk signals are ingested through secured API flows for model-ready preparation.</p>
          </article>
          <article>
            <h3>Model Layer</h3>
            <p>Versioned training runs, active-model promotion, SHAP explanations, and persisted artifacts enforce governance and repeatability.</p>
          </article>
          <article>
            <h3>Decision Layer</h3>
            <p>Predictions, agent execution traces, and scenario simulation outputs are persisted for trend analysis, audits, and executive reporting.</p>
          </article>
        </div>
      </section>

      <section className="card reveal-section">
        <h2>Why PlanetMind</h2>
        <div className="pillars">
          <div>
            <h3>Data to Decision</h3>
            <p>Move from raw climate and pandemic signals to actionable prediction outputs in a single workflow.</p>
          </div>
          <div>
            <h3>Model Governance</h3>
            <p>Version every trained model and explicitly promote active models for operational consistency.</p>
          </div>
          <div>
            <h3>Operational Clarity</h3>
            <p>Keep a persistent prediction history to support audits, trend reviews, and stakeholder reporting.</p>
          </div>
        </div>
      </section>

      <section id="contact" className="card contact-card reveal-section">
        <h2>Contact</h2>
        <p>For onboarding, platform demos, and enterprise integration requests, contact the PlanetMind team.</p>
        <div className="contact-grid">
          <div>
            <h3>Email</h3>
            <p>hello@planetmind.ai</p>
          </div>
          <div>
            <h3>Partnerships</h3>
            <p>partnerships@planetmind.ai</p>
          </div>
          <div>
            <h3>Support</h3>
            <p>support@planetmind.ai</p>
          </div>
        </div>
      </section>
    </>
  );
}
