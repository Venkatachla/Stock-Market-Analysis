/**
 * Tests for src/utils/format.ts — pure formatting utility functions.
 *
 * Covers:
 * - formatCurrency() — INR formatting with various values
 * - formatPercent() — percentage formatting with sign prefix, edge cases
 * - formatLargeNumber() — Indian number system abbreviations (Cr, L, K)
 * - getSignalColor() / getSignalBg() — CSS class mapping for BUY/SELL/NEUTRAL
 */
import { describe, it, expect } from "vitest";
import {
  formatCurrency,
  formatPercent,
  formatLargeNumber,
  getSignalColor,
  getSignalBg,
} from "@/utils/format";

describe("formatCurrency", () => {
  it("formats positive value as INR", () => {
    const result = formatCurrency(1500);
    expect(result).toContain("1,500");
    // Should contain the rupee symbol (₹ or INR indicator)
    expect(result).toMatch(/₹|INR/);
  });

  it("formats zero", () => {
    const result = formatCurrency(0);
    expect(result).toContain("0.00");
  });

  it("formats negative value", () => {
    const result = formatCurrency(-2500.5);
    expect(result).toContain("2,500.50");
  });

  it("formats large value with commas", () => {
    const result = formatCurrency(10000000);
    // In en-IN locale, 10,000,000 is "1,00,00,000"
    expect(result).toContain("00,000");
  });
});

describe("formatPercent", () => {
  it("formats positive value with + prefix", () => {
    expect(formatPercent(5.25)).toBe("+5.25%");
  });

  it("formats negative value (no + prefix)", () => {
    expect(formatPercent(-3.14)).toBe("-3.14%");
  });

  it("formats zero", () => {
    expect(formatPercent(0)).toBe("+0.00%");
  });

  it("handles undefined", () => {
    expect(formatPercent(undefined)).toBe("0.00%");
  });

  it("handles null", () => {
    expect(formatPercent(null)).toBe("0.00%");
  });

  it("handles NaN", () => {
    expect(formatPercent(NaN)).toBe("0.00%");
  });
});

describe("formatLargeNumber", () => {
  it("formats crores (≥10M)", () => {
    expect(formatLargeNumber(15000000)).toBe("1.50 Cr");
  });

  it("formats lakhs (≥100K)", () => {
    expect(formatLargeNumber(500000)).toBe("5.00 L");
  });

  it("formats thousands (≥1K)", () => {
    expect(formatLargeNumber(5000)).toBe("5.0 K");
  });

  it("returns raw value for small numbers", () => {
    expect(formatLargeNumber(999)).toBe("999");
  });

  it("formats exactly 1 crore", () => {
    expect(formatLargeNumber(10000000)).toBe("1.00 Cr");
  });
});

describe("getSignalColor", () => {
  it("returns buy color class", () => {
    expect(getSignalColor("BUY")).toBe("text-signal-buy");
  });

  it("returns sell color class", () => {
    expect(getSignalColor("SELL")).toBe("text-signal-sell");
  });

  it("returns neutral color class", () => {
    expect(getSignalColor("NEUTRAL")).toBe("text-signal-neutral");
  });
});

describe("getSignalBg", () => {
  it("returns buy background classes", () => {
    const result = getSignalBg("BUY");
    expect(result).toContain("signal-buy");
  });

  it("returns sell background classes", () => {
    const result = getSignalBg("SELL");
    expect(result).toContain("signal-sell");
  });

  it("returns neutral background classes", () => {
    const result = getSignalBg("NEUTRAL");
    expect(result).toContain("signal-neutral");
  });
});
