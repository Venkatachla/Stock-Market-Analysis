import axios, { AxiosInstance, AxiosError } from 'axios';
import type { StockPrediction, BacktestResult, PaperTrade, Signal } from '@/types';
import {
  mockPredictions,
  mockSignals,
  mockBacktestResult,
  mockPaperTrades,
  mockNewsItems,
  mockStockData,
  mockRegime,
  mockSentiment,
} from './mock-data';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;
  private backendAvailable = true;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 5000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  private isNetworkError(error: unknown): boolean {
    if (axios.isAxiosError(error)) {
      return (
        error.code === 'ECONNABORTED' ||
        error.code === 'ENOTFOUND' ||
        error.message === 'Network Error' ||
        error.response?.status === undefined
      );
    }
    return false;
  }

  isBackendAvailable(): boolean {
    return this.backendAvailable;
  }

  // Predictions
  async getPredictions(): Promise<StockPrediction[]> {
    try {
      const response = await this.client.get('/predictions');
      this.backendAvailable = true;
      return response.data;
    } catch (error) {
      if (this.isNetworkError(error)) {
        this.backendAvailable = false;
        console.warn('Backend unavailable, using mock predictions');
        return mockPredictions;
      }
      console.error('Error fetching predictions:', error);
      return mockPredictions;
    }
  }

  async getPrediction(symbol: string): Promise<StockPrediction | null> {
    try {
      const response = await this.client.get(`/prediction/${symbol}`);
      this.backendAvailable = true;
      return response.data;
    } catch (error) {
      if (this.isNetworkError(error)) {
        this.backendAvailable = false;
        console.warn(`Backend unavailable, using mock prediction for ${symbol}`);
        return mockPredictions.find(p => p.symbol === symbol) || mockPredictions[0];
      }
      console.error(`Error fetching prediction for ${symbol}:`, error);
      return mockPredictions.find(p => p.symbol === symbol) || mockPredictions[0];
    }
  }

  // Regime
  async getRegime() {
    try {
      const response = await this.client.get('/regime');
      this.backendAvailable = true;
      return response.data;
    } catch (error) {
      if (this.isNetworkError(error)) {
        this.backendAvailable = false;
        console.warn('Backend unavailable, using mock regime');
        return mockRegime;
      }
      console.error('Error fetching regime:', error);
      return mockRegime;
    }
  }

  // Backtest
  async getBacktest(symbol?: string): Promise<BacktestResult | null> {
    try {
      const url = symbol ? `/backtest/${symbol}` : '/backtest';
      const response = await this.client.get(url);
      this.backendAvailable = true;
      return response.data;
    } catch (error) {
      if (this.isNetworkError(error)) {
        this.backendAvailable = false;
        console.warn('Backend unavailable, using mock backtest');
        return mockBacktestResult;
      }
      console.error('Error fetching backtest:', error);
      return mockBacktestResult;
    }
  }

  // Paper trades
  async getPaperTrades(): Promise<PaperTrade[]> {
    try {
      const response = await this.client.get('/paper-trades');
      this.backendAvailable = true;
      return response.data;
    } catch (error) {
      if (this.isNetworkError(error)) {
        this.backendAvailable = false;
        console.warn('Backend unavailable, using mock paper trades');
        return mockPaperTrades;
      }
      console.error('Error fetching paper trades:', error);
      return mockPaperTrades;
    }
  }

  // Signals
  async getSignals(filters?: { sector?: string; regime?: string; threshold?: number }): Promise<Signal[]> {
    try {
      const response = await this.client.get('/signals', { params: filters });
      this.backendAvailable = true;
      return response.data;
    } catch (error) {
      if (this.isNetworkError(error)) {
        this.backendAvailable = false;
        console.warn('Backend unavailable, using mock signals');
        // Apply filters to mock data
        let filtered = [...mockSignals];
        if (filters?.sector) {
          filtered = filtered.filter(s => s.sector === filters.sector);
        }
        if (filters?.regime) {
          filtered = filtered.filter(s => s.regime === filters.regime);
        }
        if (filters?.threshold !== undefined) {
          filtered = filtered.filter(s => s.confidence >= filters.threshold!);
        }
        return filtered;
      }
      console.error('Error fetching signals:', error);
      return mockSignals;
    }
  }

  // Market sentiment
  async getMarketSentiment() {
    try {
      const response = await this.client.get('/sentiment');
      this.backendAvailable = true;
      return response.data;
    } catch (error) {
      if (this.isNetworkError(error)) {
        this.backendAvailable = false;
        console.warn('Backend unavailable, using mock sentiment');
        return mockSentiment;
      }
      console.error('Error fetching sentiment:', error);
      return mockSentiment;
    }
  }

  // Stock historical data
  async getStockData(symbol: string, period: string = '6m') {
    try {
      const response = await this.client.get(`/stock/${symbol}`, { params: { period } });
      this.backendAvailable = true;
      return response.data;
    } catch (error) {
      if (this.isNetworkError(error)) {
        this.backendAvailable = false;
        console.warn(`Backend unavailable, using mock stock data for ${symbol}`);
        return mockStockData(symbol);
      }
      console.error(`Error fetching stock data for ${symbol}:`, error);
      return mockStockData(symbol);
    }
  }

  // News
  async getNews(symbol: string) {
    try {
      const response = await this.client.get(`/news/${symbol}`);
      this.backendAvailable = true;
      return response.data;
    } catch (error) {
      if (this.isNetworkError(error)) {
        this.backendAvailable = false;
        console.warn(`Backend unavailable, using mock news for ${symbol}`);
        return mockNewsItems;
      }
      console.error(`Error fetching news for ${symbol}:`, error);
      return mockNewsItems;
    }
  }
}

export const apiClient = new APIClient();
