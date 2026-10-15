import { useState } from "react";
import { Nav } from "./components/Nav";
import { ViewKey } from "./types";
import { Home } from "./views/Home";
import { ModuleAnalytics } from "./views/ModuleAnalytics";
import { RiskSandbox } from "./views/RiskSandbox";
import { Explainability } from "./views/Explainability";
import { MultiAgentConsole } from "./views/MultiAgentConsole";
import { KnowledgeGraph } from "./views/KnowledgeGraph";
import { Governance } from "./views/Governance";
import "./styles.css";

export default function App() {
  const [view, setView] = useState<ViewKey>("home");

  return (
    <main className="container">
      <header className="topbar">
        <div>
          <p className="eyebrow">PlanetMind Platform</p>
          <h1>PlanetMind Intelligence Hub</h1>
          <p className="intro">Monitor risk signals, train domain models, and support proactive decisions from one web workspace.</p>
        </div>
      </header>

      <Nav view={view} onChange={setView} />

      {view === "home" ? <Home onNavigate={setView} /> : null}
      {view === "climate" ? <ModuleAnalytics module="climate" title="Climate" /> : null}
      {view === "pandemic" ? <ModuleAnalytics module="pandemic" title="Pandemic" /> : null}
      {view === "risk" ? <RiskSandbox /> : null}
      {view === "explainability" ? <Explainability /> : null}
      {view === "agents" ? <MultiAgentConsole /> : null}
      {view === "knowledge-graph" ? <KnowledgeGraph /> : null}
      {view === "governance" ? <Governance /> : null}
    </main>
  );
}
