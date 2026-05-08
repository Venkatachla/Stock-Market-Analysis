/**
 * Tests for src/components/common/StatusComponents.tsx
 *
 * Covers:
 * - LoadingState: renders message and has role="status"
 * - ErrorState: renders error message, retry button functionality
 * - MetricCard: renders label, value, and optional change indicator
 * - SignalBadge: renders BUY/SELL/NEUTRAL with correct CSS classes
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  LoadingState,
  ErrorState,
  MetricCard,
  SignalBadge,
} from "@/components/common/StatusComponents";

describe("LoadingState", () => {
  it("renders default loading message", () => {
    render(<LoadingState />);
    expect(screen.getByText("Loading...")).toBeTruthy();
  });

  it("renders custom message", () => {
    render(<LoadingState message="Fetching data..." />);
    expect(screen.getByText("Fetching data...")).toBeTruthy();
  });

  it("has role=status for accessibility", () => {
    render(<LoadingState />);
    expect(screen.getByRole("status")).toBeTruthy();
  });
});

describe("ErrorState", () => {
  it("renders error message", () => {
    render(<ErrorState message="Something went wrong" />);
    expect(screen.getByText("Something went wrong")).toBeTruthy();
  });

  it("has role=alert for accessibility", () => {
    render(<ErrorState message="Error occurred" />);
    expect(screen.getByRole("alert")).toBeTruthy();
  });

  it("renders retry button when onRetry is provided", () => {
    const onRetry = vi.fn();
    render(<ErrorState message="Failed" onRetry={onRetry} />);
    const btn = screen.getByText("Retry");
    expect(btn).toBeTruthy();
  });

  it("calls onRetry when retry button is clicked", () => {
    const onRetry = vi.fn();
    render(<ErrorState message="Failed" onRetry={onRetry} />);
    fireEvent.click(screen.getByText("Retry"));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("does not render retry button when onRetry is undefined", () => {
    render(<ErrorState message="Error" />);
    expect(screen.queryByText("Retry")).toBeNull();
  });
});

describe("MetricCard", () => {
  it("renders label and value", () => {
    render(<MetricCard label="Total Balance" value="₹1,00,000" />);
    expect(screen.getByText("Total Balance")).toBeTruthy();
    expect(screen.getByText("₹1,00,000")).toBeTruthy();
  });

  it("renders change indicator when provided", () => {
    render(
      <MetricCard label="PnL" value="₹5,000" change="+5.2%" positive={true} />
    );
    expect(screen.getByText("+5.2%")).toBeTruthy();
  });

  it("renders without change indicator", () => {
    const { container } = render(
      <MetricCard label="Holdings" value="5" />
    );
    // Should render without crashing
    expect(container.textContent).toContain("Holdings");
  });
});

describe("SignalBadge", () => {
  it("renders BUY text", () => {
    render(<SignalBadge signal="BUY" />);
    expect(screen.getByText("BUY")).toBeTruthy();
  });

  it("renders SELL text", () => {
    render(<SignalBadge signal="SELL" />);
    expect(screen.getByText("SELL")).toBeTruthy();
  });

  it("renders NEUTRAL text", () => {
    render(<SignalBadge signal="NEUTRAL" />);
    expect(screen.getByText("NEUTRAL")).toBeTruthy();
  });

  it("applies buy-specific CSS classes", () => {
    const { container } = render(<SignalBadge signal="BUY" />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("signal-buy");
  });

  it("applies sell-specific CSS classes", () => {
    const { container } = render(<SignalBadge signal="SELL" />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("signal-sell");
  });
});
