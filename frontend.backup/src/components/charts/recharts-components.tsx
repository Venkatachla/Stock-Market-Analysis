'use client';

import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface EquityChartProps {
  data: Array<{ date: string; equity: number }>;
}

export function EquityChart({ data }: EquityChartProps) {
  return (
    <div className="w-full h-64 bg-trading-card border border-gray-700/50 rounded-lg p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
          <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
          <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #4b5563',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#fff' }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="equity"
            stroke="#10b981"
            dot={false}
            strokeWidth={2}
            name="Portfolio Value"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

interface DrawdownChartProps {
  data: Array<{ date: string; drawdown: number }>;
}

export function DrawdownChart({ data }: DrawdownChartProps) {
  return (
    <div className="w-full h-64 bg-trading-card border border-gray-700/50 rounded-lg p-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
          <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
          <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #4b5563',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#fff' }}
          />
          <Area
            type="monotone"
            dataKey="drawdown"
            stroke="#ef4444"
            fill="#ef4444"
            fillOpacity={0.2}
            name="Drawdown"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

interface PnLChartProps {
  data: Array<{ date: string; pnl: number }>;
}

export function PnLChart({ data }: PnLChartProps) {
  return (
    <div className="w-full h-64 bg-trading-card border border-gray-700/50 rounded-lg p-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
          <XAxis dataKey="date" stroke="#9ca3af" style={{ fontSize: '12px' }} />
          <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #4b5563',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#fff' }}
          />
          <Bar
            dataKey="pnl"
            fill="#3b82f6"
            radius={[4, 4, 0, 0]}
            name="Daily PnL"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface TradeReturnsChartProps {
  data: Array<{ return: number; count: number }>;
}

export function TradeReturnsHistogram({ data }: TradeReturnsChartProps) {
  return (
    <div className="w-full h-64 bg-trading-card border border-gray-700/50 rounded-lg p-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
          <XAxis dataKey="return" stroke="#9ca3af" style={{ fontSize: '12px' }} />
          <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #4b5563',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#fff' }}
          />
          <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
