import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Portfolio from '@/pages/Portfolio';
import * as api from '@/services/api';

// Mock dependencies
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ token: 'mock-token' })
}));

vi.mock('react-router-dom', () => ({
  Link: ({ children, to }: any) => <a href={to}>{children}</a>
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
});

describe('Portfolio Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "Please log in" when no token is present', () => {
    // Override the mock just for this test
    vi.doMock('@/contexts/AuthContext', () => ({
      useAuth: () => ({ token: null })
    }));
    
    // We need to re-import the component since the mock changed
    vi.resetModules();
    const PortfolioNoAuth = require('@/pages/Portfolio').default;
    
    render(
      <QueryClientProvider client={queryClient}>
        <PortfolioNoAuth />
      </QueryClientProvider>
    );
    
    expect(screen.getByText(/Please log in to view your portfolio/i)).toBeInTheDocument();
  });

  it('renders portfolio dashboard with wallet data', async () => {
    vi.doMock('@/contexts/AuthContext', () => ({
      useAuth: () => ({ token: 'mock-token' })
    }));
    vi.resetModules();
    const PortfolioComponent = require('@/pages/Portfolio').default;

    // Mock API responses
    vi.spyOn(api, 'getWallet').mockResolvedValue({
      available_balance: 5000,
      used_balance: 1000,
      total_balance: 6000
    });

    vi.spyOn(api, 'getPortfolio').mockResolvedValue({
      wallet: { available_balance: 5000, used_balance: 1000, total_balance: 6000 },
      portfolio_value: 10000,
      total_invested: 8000,
      pnl: 2000,
      pnl_percent: 25,
      holdings: [
        {
          symbol: 'TCS',
          name: 'Tata Consultancy Services',
          quantity: 10,
          avgPrice: 3000,
          currentPrice: 3500,
          pnl: 5000,
          pnlPercent: 16.67,
          allocation: 100,
          signal: 'BUY'
        }
      ],
      number_of_holdings: 1
    });

    vi.spyOn(api, 'getTransactions').mockResolvedValue([]);

    render(
      <QueryClientProvider client={queryClient}>
        <PortfolioComponent />
      </QueryClientProvider>
    );

    // Wait for the data to load
    await waitFor(() => {
      expect(screen.getByText('Portfolio')).toBeInTheDocument();
    });

    // Check if holdings are rendered
    await waitFor(() => {
      expect(screen.getByText('TCS')).toBeInTheDocument();
    });
  });
});
