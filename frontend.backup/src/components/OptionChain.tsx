import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

interface StrikeData {
  strike: number;
  call: { oi: number; chng_oi: number; volume: number; iv: number; ltp: number; chng: number };
  put: { oi: number; chng_oi: number; volume: number; iv: number; ltp: number; chng: number };
}

interface OptionChainProps {
  symbol: string;
  onClose: () => void;
}

export function OptionChain({ symbol, onClose }: OptionChainProps) {
  const [data, setData] = useState<{ spot: number; expiry: string; chain: StrikeData[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchChain = async () => {
      try {
        const res = await axios.get(`${API_URL}/options/chain/${encodeURIComponent(symbol)}`);
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchChain();
  }, [symbol]);

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-800">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              Option Chain: <span className="text-blue-400">{symbol}</span>
            </h2>
            {data && (
              <div className="text-sm text-gray-400 mt-1 flex gap-4">
                <span>Spot Price: <strong className="text-white">₹{data.spot.toLocaleString('en-IN')}</strong></span>
                <span>Expiry: <strong className="text-white">{data.expiry}</strong></span>
              </div>
            )}
          </div>
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors">
            ✕ Close
          </button>
        </div>

        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="flex justify-center items-center h-64 text-gray-400">Loading F&O Data...</div>
          ) : !data || data.chain.length === 0 ? (
            <div className="flex justify-center items-center h-64 text-gray-400">Data unavailable for {symbol}</div>
          ) : (
            <table className="w-full text-sm text-right border-collapse">
              <thead className="bg-gray-800 sticky top-0 z-10 shadow-md">
                <tr>
                  <th colSpan={6} className="text-center py-2 px-3 border-b border-r border-gray-700 bg-green-900/20 text-green-400">CALLS</th>
                  <th className="text-center py-2 px-3 border-b border-r border-gray-700 bg-gray-700 text-white">STRIKE</th>
                  <th colSpan={6} className="text-center py-2 px-3 border-b border-gray-700 bg-red-900/20 text-red-400">PUTS</th>
                </tr>
                <tr className="text-gray-400 font-medium bg-gray-800/80">
                  <th className="py-2 px-3 border-b border-gray-700 border-r">OI</th>
                  <th className="py-2 px-3 border-b border-gray-700 border-r">Chng OI</th>
                  <th className="py-2 px-3 border-b border-gray-700 border-r">Volume</th>
                  <th className="py-2 px-3 border-b border-gray-700 border-r">IV</th>
                  <th className="py-2 px-3 border-b border-gray-700 border-r">LTP</th>
                  <th className="py-2 px-3 border-b border-gray-700 border-r">Chng</th>
                  
                  <th className="py-2 px-3 border-b border-gray-700 border-r text-center font-bold text-white bg-gray-700">Strike</th>
                  
                  <th className="py-2 px-3 border-b border-gray-700 border-r">LTP</th>
                  <th className="py-2 px-3 border-b border-gray-700 border-r">Chng</th>
                  <th className="py-2 px-3 border-b border-gray-700 border-r">IV</th>
                  <th className="py-2 px-3 border-b border-gray-700 border-r">Volume</th>
                  <th className="py-2 px-3 border-b border-gray-700 border-r">Chng OI</th>
                  <th className="py-2 px-3 border-b border-gray-700">OI</th>
                </tr>
              </thead>
              <tbody className="bg-gray-900">
                {data.chain.map((row, i) => {
                  const isITMCall = row.strike < data.spot;
                  const isITMPut = row.strike > data.spot;
                  return (
                    <tr key={i} className="hover:bg-gray-800 transition-colors border-b border-gray-800">
                      {/* Calls */}
                      <td className={`py-2 px-3 border-r border-gray-800 ${isITMCall ? 'bg-yellow-900/10' : ''}`}>{row.call.oi.toLocaleString()}</td>
                      <td className={`py-2 px-3 border-r border-gray-800 ${isITMCall ? 'bg-yellow-900/10' : ''} ${row.call.chng_oi > 0 ? 'text-green-400' : 'text-red-400'}`}>{row.call.chng_oi > 0 ? '+' : ''}{row.call.chng_oi.toLocaleString()}</td>
                      <td className={`py-2 px-3 border-r border-gray-800 ${isITMCall ? 'bg-yellow-900/10' : ''}`}>{row.call.volume.toLocaleString()}</td>
                      <td className={`py-2 px-3 border-r border-gray-800 ${isITMCall ? 'bg-yellow-900/10' : ''}`}>{row.call.iv}</td>
                      <td className={`py-2 px-3 border-r border-gray-800 font-semibold text-green-400 ${isITMCall ? 'bg-yellow-900/10' : ''}`}>{row.call.ltp.toFixed(2)}</td>
                      <td className={`py-2 px-3 border-r border-gray-700 ${row.call.chng >= 0 ? 'text-green-400' : 'text-red-400'} ${isITMCall ? 'bg-yellow-900/10' : ''}`}>{row.call.chng >= 0 ? '+' : ''}{row.call.chng.toFixed(2)}</td>
                      
                      {/* Strike */}
                      <td className="py-2 px-3 border-r border-gray-700 text-center font-bold text-gray-200 bg-gray-800/50">{row.strike.toLocaleString('en-IN')}</td>
                      
                      {/* Puts */}
                      <td className={`py-2 px-3 border-r border-gray-800 font-semibold text-red-400 ${isITMPut ? 'bg-yellow-900/10' : ''}`}>{row.put.ltp.toFixed(2)}</td>
                      <td className={`py-2 px-3 border-r border-gray-800 ${row.put.chng >= 0 ? 'text-green-400' : 'text-red-400'} ${isITMPut ? 'bg-yellow-900/10' : ''}`}>{row.put.chng >= 0 ? '+' : ''}{row.put.chng.toFixed(2)}</td>
                      <td className={`py-2 px-3 border-r border-gray-800 ${isITMPut ? 'bg-yellow-900/10' : ''}`}>{row.put.iv}</td>
                      <td className={`py-2 px-3 border-r border-gray-800 ${isITMPut ? 'bg-yellow-900/10' : ''}`}>{row.put.volume.toLocaleString()}</td>
                      <td className={`py-2 px-3 border-r border-gray-800 ${isITMPut ? 'bg-yellow-900/10' : ''} ${row.put.chng_oi > 0 ? 'text-green-400' : 'text-red-400'}`}>{row.put.chng_oi > 0 ? '+' : ''}{row.put.chng_oi.toLocaleString()}</td>
                      <td className={`py-2 px-3 ${isITMPut ? 'bg-yellow-900/10' : ''}`}>{row.put.oi.toLocaleString()}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
