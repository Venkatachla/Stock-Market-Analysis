/**
 * Tests for src/utils/mockData.ts — mock data generators and shapes.
 *
 * Covers:
 * - generateMockOHLC() — generates valid OHLC candlestick data
 * - generateMockIndicators() — generates technical indicator arrays
 * - Static mock data shape validation (mockSignals, mockPortfolio, mockRisk, mockMarketOverview)
 */
import { describe, it, expect } from "vitest";
import {
  generateMockOHLC,
  generateMockIndicators,
  mockSignals,
  mockPortfolio,
  mockRisk,
  mockMarketOverview,
} from "@/utils/mockData";

describe("generateMockOHLC", () => {
  it("returns an array of OHLC entries", () => {
    const data = generateMockOHLC(30);
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);
  });

  it("each entry has required OHLC fields", () => {
    const data = generateMockOHLC(10);
    for (const entry of data) {
      expect(entry).toHaveProperty("time");
      expect(entry).toHaveProperty("open");
      expect(entry).toHaveProperty("high");
      expect(entry).toHaveProperty("low");
      expect(entry).toHaveProperty("close");
      expect(entry).toHaveProperty("volume");
    }
  });

  it("high is always >= low for each candle", () => {
    const data = generateMockOHLC(50);
    for (const entry of data) {
      expect(entry.high).toBeGreaterThanOrEqual(entry.low);
    }
  });

  it("skips weekends (no Saturday/Sunday)", () => {
    const data = generateMockOHLC(30);
    for (const entry of data) {
      const day = new Date(entry.time).getDay();
      expect(day).not.toBe(0); // Sunday
      expect(day).not.toBe(6); // Saturday
    }
  });

  it("defaults to 250 trading days", () => {
    const data = generateMockOHLC();
    // ~250 trading days - weekends ≈ 178 entries (varies)
    expect(data.length).toBeGreaterThan(100);
  });
});

describe("generateMockIndicators", () => {
  it("returns all indicator arrays", () => {
    const ohlc = generateMockOHLC(30);
    const indicators = generateMockIndicators(ohlc);
    expect(indicators).toHaveProperty("sma20");
    expect(indicators).toHaveProperty("sma50");
    expect(indicators).toHaveProperty("ema12");
    expect(indicators).toHaveProperty("ema26");
    expect(indicators).toHaveProperty("rsi");
    expect(indicators).toHaveProperty("macd");
    expect(indicators).toHaveProperty("bollingerBands");
  });

  it("sma arrays have same length as input", () => {
    const ohlc = generateMockOHLC(30);
    const indicators = generateMockIndicators(ohlc);
    expect(indicators.sma20.length).toBe(ohlc.length);
  });
});

describe("mockSignals", () => {
  it("is a non-empty array", () => {
    expect(mockSignals.length).toBeGreaterThan(0);
  });

  it("each signal has required fields", () => {
    for (const s of mockSignals) {
      expect(s).toHaveProperty("symbol");
      expect(s).toHaveProperty("price");
      expect(s).toHaveProperty("signal");
      expect(s).toHaveProperty("confidence");
    }
  });
});

describe("mockPortfolio", () => {
  it("contains portfolio holdings", () => {
    expect(mockPortfolio.length).toBeGreaterThan(0);
  });

  it("each holding has required fields", () => {
    for (const h of mockPortfolio) {
      expect(h).toHaveProperty("symbol");
      expect(h).toHaveProperty("quantity");
      expect(h).toHaveProperty("avgPrice");
      expect(h).toHaveProperty("currentPrice");
      expect(h).toHaveProperty("pnl");
    }
  });
});

describe("mockRisk", () => {
  it("has risk metric fields", () => {
    expect(mockRisk).toHaveProperty("sharpeRatio");
    expect(mockRisk).toHaveProperty("beta");
    expect(mockRisk).toHaveProperty("maxDrawdown");
    expect(mockRisk).toHaveProperty("volatility");
    expect(mockRisk).toHaveProperty("correlationMatrix");
  });
});

describe("mockMarketOverview", () => {
  it("has indices, gainers, losers, active", () => {
    expect(mockMarketOverview).toHaveProperty("indices");
    expect(mockMarketOverview).toHaveProperty("topGainers");
    expect(mockMarketOverview).toHaveProperty("topLosers");
    expect(mockMarketOverview).toHaveProperty("mostActive");
  });

  it("indices is non-empty", () => {
    expect(mockMarketOverview.indices.length).toBeGreaterThan(0);
  });
});
