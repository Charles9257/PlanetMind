import { ViewKey } from "../types";

const NAV_ITEMS: Array<{ key: ViewKey; label: string }> = [
  { key: "home", label: "Home" },
  { key: "climate", label: "Climate Analytics" },
  { key: "pandemic", label: "Pandemic Analytics" },
  { key: "risk", label: "Risk Sandbox" },
  { key: "explainability", label: "Explainability" },
  { key: "agents", label: "Multi-Agent Console" },
  { key: "knowledge-graph", label: "Knowledge Graph" },
  { key: "governance", label: "Governance" }
];

export function Nav({ view, onChange }: { view: ViewKey; onChange: (view: ViewKey) => void }) {
  return (
    <nav className="switcher">
      {NAV_ITEMS.map((item) => (
        <button
          key={item.key}
          type="button"
          className={view === item.key ? "active" : ""}
          onClick={() => onChange(item.key)}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
