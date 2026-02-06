import { render, fireEvent } from "@solidjs/testing-library";
import { describe, it, expect, vi } from "vitest";
import { Button } from "./Button";

describe("Button", () => {
  it("renders with default variant and size", () => {
    const { container } = render(() => <Button>Click me</Button>);
    const button = container.querySelector('[data-slot="button"]');

    expect(button).not.toBeNull();
    expect(button?.textContent).toBe("Click me");
    const className = button?.className || "";
    expect(className).toContain("bg-primary");
    expect(className).toContain("h-9");
  });

  it("renders with destructive variant", () => {
    const { container } = render(() => <Button variant="destructive">Delete</Button>);
    const button = container.querySelector('[data-slot="button"]');

    const className = button?.className || "";
    expect(className).toContain("bg-destructive");
  });

  it("renders with outline variant", () => {
    const { container } = render(() => <Button variant="outline">Cancel</Button>);
    const button = container.querySelector('[data-slot="button"]');

    const className = button?.className || "";
    expect(className).toContain("border");
  });

  it("renders with small size", () => {
    const { container } = render(() => <Button size="sm">Small</Button>);
    const button = container.querySelector('[data-slot="button"]');

    const className = button?.className || "";
    expect(className).toContain("h-8");
  });

  it("renders with large size", () => {
    const { container } = render(() => <Button size="lg">Large</Button>);
    const button = container.querySelector('[data-slot="button"]');

    const className = button?.className || "";
    expect(className).toContain("h-10");
  });

  it("handles click events", () => {
    const handleClick = vi.fn();
    const { container } = render(() => <Button onClick={handleClick}>Click</Button>);
    const button = container.querySelector('[data-slot="button"]') as HTMLButtonElement;

    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("can be disabled", () => {
    const { container } = render(() => <Button disabled>Disabled</Button>);
    const button = container.querySelector('[data-slot="button"]') as HTMLButtonElement;

    expect(button.disabled).toBe(true);
    const className = button?.className || "";
    expect(className).toContain("disabled:opacity-50");
  });

  it("renders as a button element", () => {
    const { container } = render(() => <Button>Test</Button>);
    const button = container.querySelector('[data-slot="button"]');

    expect(button?.tagName).toBe("BUTTON");
  });
});
