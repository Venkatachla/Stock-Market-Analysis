import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Signup from './Signup';

// Mock the AuthContext
vi.mock('@/contexts/AuthContext', async () => {
  const actual = await vi.importActual<typeof import('@/contexts/AuthContext')>('@/contexts/AuthContext');
  return {
    ...actual,
    useAuth: () => ({
      signup: vi.fn().mockResolvedValue({}),
      isAuthenticated: false,
    }),
  };
});

describe('Signup Component', () => {
  const renderSignup = () => {
    return render(
      <BrowserRouter>
        <Signup />
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the signup form correctly', () => {
    renderSignup();
    expect(screen.getByRole('heading', { name: /Create Account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Confirm Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeInTheDocument();
  });

  it('shows error when passwords do not match', async () => {
    renderSignup();
    
    fireEvent.change(screen.getByLabelText(/Email Address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/^Password/i), { target: { value: 'password123' } });
    fireEvent.change(screen.getByLabelText(/Confirm Password/i), { target: { value: 'password456' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
    });
  });

  it('shows error on invalid email using safe regex', async () => {
    renderSignup();
    
    fireEvent.change(screen.getByLabelText(/Email Address/i), { target: { value: 'invalid-email' } });
    fireEvent.change(screen.getByLabelText(/^Password/i), { target: { value: 'password123' } });
    fireEvent.change(screen.getByLabelText(/Confirm Password/i), { target: { value: 'password123' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid email address/i)).toBeInTheDocument();
    });
  });
});
