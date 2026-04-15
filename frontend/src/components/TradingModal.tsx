import React, { useState, useMemo } from 'react';
import { X, AlertCircle, TrendingUp, Wallet } from 'lucide-react';
import { buyStock, sellStock, getWallet, Wallet as WalletType } from '@/services/api';

interface TradingModalProps {
  isOpen: boolean;
  onClose: () => void;
  symbol: string;
  currentPrice: number;
  mode: 'BUY' | 'SELL';
  maxQuantity?: number;
  token: string;
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
}

export const TradingModal: React.FC<TradingModalProps> = ({
  isOpen,
  onClose,
  symbol,
  currentPrice,
  mode,
  maxQuantity = 1000,
  token,
  onSuccess,
  onError,
}) => {
  const [quantity, setQuantity] = useState('1');
  const [loading, setLoading] = useState(false);
  const [wallet, setWallet] = useState<WalletType | null>(null);

  // Fetch wallet on mount
  React.useEffect(() => {
    if (isOpen) {
      getWallet(token)
        .then(setWallet)
        .catch(() => {
          onError('Failed to load wallet');
        });
    }
  }, [isOpen, token, onError]);

  const quantityNum = parseInt(quantity) || 0;
  const totalCost = quantityNum * currentPrice;

  const stats = useMemo(() => {
    const canAfford = wallet ? totalCost <= wallet.available_balance : false;
    const canSell = quantityNum <= maxQuantity;

    return {
      totalCost,
      canAfford,
      canSell,
      hasError: mode === 'BUY' && !canAfford ? 'Insufficient balance' : 
                mode === 'SELL' && !canSell ? 'Insufficient quantity' : null,
    };
  }, [quantityNum, totalCost, wallet, maxQuantity, mode]);

  const handleSubmit = async () => {
    if (quantityNum <= 0) {
      onError('Quantity must be greater than 0');
      return;
    }

    if (stats.hasError) {
      onError(stats.hasError);
      return;
    }

    setLoading(true);

    try {
      if (mode === 'BUY') {
        await buyStock(token, symbol, quantityNum);
        onSuccess(`Successfully bought ${quantityNum} shares of ${symbol} at ₹${currentPrice}`);
      } else {
        await sellStock(token, symbol, quantityNum);
        onSuccess(`Successfully sold ${quantityNum} shares of ${symbol} at ₹${currentPrice}`);
      }
      setQuantity('1');
      onClose();
    } catch (error: any) {
      onError(error.response?.data?.detail || `Failed to ${mode === 'BUY' ? 'buy' : 'sell'}`);
    } finally {
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
            {mode === 'BUY' ? <TrendingUp className="h-6 w-6 text-green-500" /> : <TrendingUp className="h-6 w-6 text-red-500" />}
            {mode} {symbol}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition"
            disabled={loading}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Current Price */}
        <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
          <p className="text-slate-400 text-sm">Current Price</p>
          <p className="text-2xl font-bold text-white">₹{currentPrice.toFixed(2)}</p>
        </div>

        {/* Quantity Input */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Quantity
          </label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            min="1"
            max={mode === 'SELL' ? maxQuantity : undefined}
            className="w-full px-4 py-2 rounded-lg bg-slate-700 border border-slate-600 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          {mode === 'SELL' && (
            <p className="text-xs text-slate-400 mt-1">Available: {maxQuantity} shares</p>
          )}
        </div>

        {/* Total Cost */}
        <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
          <div className="flex justify-between items-center mb-3">
            <p className="text-slate-400">Quantity</p>
            <p className="text-white font-medium">{quantityNum}</p>
          </div>
          <div className="flex justify-between items-center mb-3 pb-3 border-b border-slate-600">
            <p className="text-slate-400">Price per share</p>
            <p className="text-white font-medium">₹{currentPrice.toFixed(2)}</p>
          </div>
          <div className="flex justify-between items-center">
            <p className="text-slate-300 font-medium">Total {mode === 'BUY' ? 'Cost' : 'Proceeds'}</p>
            <p className={`text-lg font-bold ${mode === 'BUY' ? 'text-red-400' : 'text-green-400'}`}>
              ₹{stats.totalCost.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Wallet Info (for BUY) */}
        {mode === 'BUY' && wallet && (
          <div className="bg-blue-500/10 rounded-lg p-3 mb-6 border border-blue-500/20 flex items-start gap-3">
            <Wallet className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-300">
              <p>Available Balance: <span className="font-semibold">₹{wallet.available_balance.toFixed(2)}</span></p>
              <p>After Purchase: <span className="font-semibold text-blue-200">₹{(wallet.available_balance - stats.totalCost).toFixed(2)}</span></p>
            </div>
          </div>
        )}

        {/* Error Message */}
        {stats.hasError && (
          <div className="bg-red-500/10 rounded-lg p-3 mb-6 border border-red-500/20 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-300">{stats.hasError}</p>
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 rounded-lg bg-slate-700 text-slate-200 font-medium hover:bg-slate-600 transition disabled:opacity-50"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !!stats.hasError}
            className={`flex-1 px-4 py-2 rounded-lg font-medium text-white transition disabled:opacity-50 ${
              mode === 'BUY'
                ? 'bg-green-600 hover:bg-green-700'
                : 'bg-red-600 hover:bg-red-700'
            }`}
          >
            {loading ? 'Processing...' : `${mode} ${symbol}`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TradingModal;
