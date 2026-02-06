import { render } from "@solidjs/testing-library";
import { describe, it, expect } from "vitest";
import { Badge } from "./Badge";

describe("Badge", () => {
  it("renders with default variant", () => {
    const { container } = render(() => <Badge>Default</Badge>);
    const badge = container.querySelector('[data-slot="badge"]');

    expect(badge).not.toBeNull();
    expect(badge?.textContent).toBe("Default");
    const className = badge?.className || "";
    expect(className).toContain("bg-primary");
  });

  it("renders with secondary variant", () => {
    const { container } = render(() => <Badge variant="secondary">Secondary</Badge>);
    const badge = container.querySelector('[data-slot="badge"]');

    const className = badge?.className || "";
    expect(className).toContain("bg-secondary");
  });

  it("renders with destructive variant", () => {
    const { container } = render(() => <Badge variant="destructive">Error</Badge>);
    const badge = container.querySelector('[data-slot="badge"]');

    const className = badge?.className || "";
    expect(className).toContain("bg-destructive");
  });

  it("renders with outline variant", () => {
    const { container } = render(() => <Badge variant="outline">Outline</Badge>);
    const badge = container.querySelector('[data-slot="badge"]');

    const className = badge?.className || "";
    expect(className).toContain("text-foreground");
  });

  it("accepts custom class", () => {
    const { container } = render(() => <Badge class="custom-badge">Custom</Badge>);
    const badge = container.querySelector('[data-slot="badge"]');

    const className = badge?.className || "";
    expect(className).toContain("custom-badge");
  });

  it("renders as a span element", () => {
    const { container } = render(() => <Badge>Test</Badge>);
    const badge = container.querySelector('[data-slot="badge"]');

    expect(badge?.tagName).toBe("SPAN");
  });
});
