import { render } from "@solidjs/testing-library";
import { describe, it, expect } from "vitest";
import { Skeleton } from "./Skeleton";

describe("Skeleton", () => {
  it("renders with default classes", () => {
    const { container } = render(() => <Skeleton />);
    const skeleton = container.querySelector('[data-slot="skeleton"]');

    expect(skeleton).not.toBeNull();
    const className = skeleton?.className || "";
    expect(className).toContain("bg-accent");
    expect(className).toContain("animate-pulse");
    expect(className).toContain("rounded-md");
  });

  it("accepts custom class", () => {
    const { container } = render(() => <Skeleton class="custom-class w-full" />);
    const skeleton = container.querySelector('[data-slot="skeleton"]');

    expect(skeleton).not.toBeNull();
    const className = skeleton?.className || "";
    expect(className).toContain("custom-class");
    expect(className).toContain("w-full");
    expect(className).toContain("bg-accent");
  });

  it("spreads additional props", () => {
    const { container } = render(() => (
      <Skeleton data-testid="test-skeleton" aria-label="Loading" />
    ));
    const skeleton = container.querySelector('[data-testid="test-skeleton"]');

    expect(skeleton).not.toBeNull();
    expect(skeleton?.getAttribute("aria-label")).toBe("Loading");
  });

  it("renders as a div element", () => {
    const { container } = render(() => <Skeleton />);
    const skeleton = container.querySelector('[data-slot="skeleton"]');

    expect(skeleton?.tagName).toBe("DIV");
  });
});
