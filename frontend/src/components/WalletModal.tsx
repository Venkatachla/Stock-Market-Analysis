import React, { useState, useEffect } from 'react';
import { X, Wallet as WalletIcon, CreditCard, CheckCircle, AlertCircle } from 'lucide-react';
import { createPaymentOrder, verifyPayment, getWallet, addDemoFunds, Wallet } from '@/services/api';

interface WalletModalProps {
  isOpen: boolean;
  onClose: () => void;
  token: string;
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
  onWalletUpdate?: (wallet: Wallet) => void;
}

declare global {
  interface Window {
    Razorpay: new (options: unknown) => { open: () => void };
  }
}

export const WalletModal: React.FC<WalletModalProps> = ({
  isOpen,
  onClose,
  token,
  onSuccess,
  onError,
  onWalletUpdate,
}) => {
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [amount, setAmount] = useState('1000');
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<'view' | 'add'>('view');

  // Fetch wallet on open
  useEffect(() => {
    if (isOpen) {
      getWallet(token)
        .then(setWallet)
        .catch(() => onError('Failed to load wallet'));
    }
  }, [isOpen, token, onError]);

  const handleAddDemoFunds = async () => {
    const amountNum = parseFloat(amount);
    if (amountNum <= 0) {
      onError('Amount must be greater than 0');
      return;
    }

    setLoading(true);
    try {
      await addDemoFunds(token, amountNum);
      const updatedWallet = await getWallet(token);
      setWallet(updatedWallet);
      onWalletUpdate?.(updatedWallet);
      onSuccess(`₹${amountNum} added to wallet (Demo)`);
      setAmount('1000');
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      onError(detail || 'Failed to add funds');
    } finally {
      setLoading(false);
    }
  };

  const handleRazorpayPayment = async () => {
    const amountNum = parseFloat(amount);
    if (amountNum <= 0) {
      onError('Amount must be greater than 0');
      return;
    }

    setLoading(true);
    try {
      // Create order
      const orderData = await createPaymentOrder(token, amountNum);

      if (!window.Razorpay) {
        onError('Razorpay not available. Use demo funds instead.');
        setLoading(false);
        return;
      }

      const options = {
        key: orderData.key_id,
        amount: Math.round(amountNum * 100), // Amount in paise
        currency: 'INR',
        order_id: orderData.order_id,
        handler: async (response: { razorpay_payment_id: string; razorpay_signature: string }) => {
          try {
            // Verify payment
            await verifyPayment(token, {
              order_id: orderData.order_id,
              payment_id: response.razorpay_payment_id,
              signature: response.razorpay_signature,
            });

            // Update wallet
            const updatedWallet = await getWallet(token);
            setWallet(updatedWallet);
            onWalletUpdate?.(updatedWallet);
            onSuccess(`₹${amountNum} added to wallet`);
            setAmount('1000');
          } catch (error: unknown) {
            const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            onError(detail || 'Payment verification failed');
          } finally {
            setLoading(false);  // Always reset loading after payment handler completes
          }
        },
        prefill: {
          contact: '9999999999',
          email: 'user@example.com',
        },
        theme: {
          color: '#3b82f6',
        },
        modal: {
          ondismiss: () => {
            setLoading(false);
            onError('Payment cancelled');
          },
        },
      };

      new window.Razorpay(options).open();
    } catch (error: unknown) {
      const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      onError(detail || 'Failed to create payment order');
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-lg border border-slate-700 max-w-md w-full p-6 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <WalletIcon className="h-6 w-6 text-blue-400" />
            Wallet
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition"
            disabled={loading}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-slate-700">
          <button
            onClick={() => setTab('view')}
            className={`px-4 py-2 font-medium border-b-2 transition ${
              tab === 'view'
                ? 'text-blue-400 border-blue-400'
                : 'text-slate-400 border-transparent hover:text-slate-300'
            }`}
          >
            View Balance
          </button>
          <button
            onClick={() => setTab('add')}
            className={`px-4 py-2 font-medium border-b-2 transition ${
              tab === 'add'
                ? 'text-blue-400 border-blue-400'
                : 'text-slate-400 border-transparent hover:text-slate-300'
            }`}
          >
            Add Funds
          </button>
        </div>

        {tab === 'view' ? (
          <>
            {/* Balance View */}
            <div className="space-y-4">
              <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg p-6 border border-blue-500/20">
                <p className="text-slate-400 text-sm">Total Balance</p>
                <p className="text-4xl font-bold text-blue-300 mt-2">
                  ₹{typeof wallet?.total_balance === "number" ? wallet.total_balance.toFixed(2) : "0.00"}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <p className="text-slate-400 text-xs">Available</p>
                  <p className="text-lg font-bold text-green-400 mt-2">
                  ₹{typeof wallet?.available_balance === "number" ? wallet.available_balance.toFixed(2) : "0.00"}
                  </p>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <p className="text-slate-400 text-xs">Used</p>
                  <p className="text-lg font-bold text-orange-400 mt-2">
                  ₹{typeof wallet?.used_balance === "number" ? wallet.used_balance.toFixed(2) : "0.00"}
                  </p>
                </div>
              </div>

              <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                <p className="text-slate-400 text-sm">
                  Your wallet shows the total balance available for trading. Start by adding funds to begin your trading journey.
                </p>
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Add Funds */}
            <div className="space-y-4">
              {/* Amount Input */}
              <div>
                <label htmlFor="wallet-amount" className="block text-sm font-medium text-slate-300 mb-2">
                  Amount (₹)
                </label>
                <div className="flex gap-2">
                  <input
                    id="wallet-amount"
                    name="amount"
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    min="100"
                    max="100000"
                    step="100"
                    className="flex-1 px-4 py-2 rounded-lg bg-slate-700 border border-slate-600 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={loading}
                  />
                </div>
                <p className="text-xs text-slate-400 mt-1">Minimum ₹100, Maximum ₹100,000</p>
              </div>

              {/* Quick Amount Buttons */}
              <div>
                <p className="text-xs text-slate-400 mb-2">Quick add</p>
                <div className="grid grid-cols-4 gap-2">
                  {['1000', '5000', '10000', '20000'].map((val) => (
                    <button
                      key={val}
                      onClick={() => setAmount(val)}
                      className="px-3 py-2 rounded bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium transition"
                      disabled={loading}
                    >
                      ₹{val}
                    </button>
                  ))}
                </div>
              </div>

              {/* Demo Funds Button */}
              <button
                onClick={handleAddDemoFunds}
                disabled={loading}
                className="w-full py-2 px-4 rounded-lg bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white font-medium transition flex items-center justify-center gap-2"
              >
                <CheckCircle className="h-4 w-4" />
                Add Demo Funds
              </button>

              {/* Razorpay Payment Button */}
              <div>
                <p className="text-xs text-slate-400 mb-2">Or pay with card/UPI</p>
                <button
                  onClick={handleRazorpayPayment}
                  disabled={loading}
                  className="w-full py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-medium transition flex items-center justify-center gap-2"
                >
                  <CreditCard className="h-4 w-4" />
                  Pay with Razorpay
                </button>
              </div>

              {/* Info */}
              <div className="bg-yellow-500/10 rounded-lg p-3 border border-yellow-500/20 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-yellow-300">
                  Demo funds are for testing only. Use Razorpay for real transactions.
                </p>
              </div>
            </div>
          </>
        )}

        {/* Message */}
        {tab === 'view' && (
          <div className="mt-6 pt-6 border-t border-slate-700">
            <button
              onClick={() => setTab('add')}
              className="w-full py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition"
            >
              Add Funds
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default WalletModal;
