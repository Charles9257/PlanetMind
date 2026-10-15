import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Nav } from "./Nav";

describe("Nav", () => {
  it("marks the active view and calls onChange when a different tab is clicked", () => {
    const onChange = vi.fn();
    render(<Nav view="climate" onChange={onChange} />);

    const climateButton = screen.getByRole("button", { name: "Climate Analytics" });
    expect(climateButton.className).toContain("active");

    const governanceButton = screen.getByRole("button", { name: "Governance" });
    expect(governanceButton.className).not.toContain("active");

    fireEvent.click(governanceButton);
    expect(onChange).toHaveBeenCalledWith("governance");
  });

  it("renders a tab for every core module", () => {
    render(<Nav view="home" onChange={() => undefined} />);
    for (const label of [
      "Home",
      "Climate Analytics",
      "Pandemic Analytics",
      "Risk Sandbox",
      "Explainability",
      "Multi-Agent Console",
      "Knowledge Graph",
      "Governance"
    ]) {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    }
  });
});
