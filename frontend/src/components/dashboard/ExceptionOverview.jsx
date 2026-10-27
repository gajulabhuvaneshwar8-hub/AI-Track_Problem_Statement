import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import StatusBadge from '../common/StatusBadge'

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#f59e0b',
  low: '#3b82f6',
}

export default function ExceptionOverview({ exceptionData }) {
  if (!exceptionData) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-center h-64 text-xs text-slate-500">
        Exception metrics not available
      </div>
    )
  }

  const severities = exceptionData.by_severity || []
  const chartData = severities.map((s) => ({
    name: s.label || s.key,
    count: s.count,
    key: s.key,
  }))

  const categories = exceptionData.by_category || []
  const hasData = chartData.some((d) => d.count > 0)

  return (
    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">Exception Distribution</h3>
          <p className="text-xs text-slate-400 mt-0.5">Active mismatches by operational severity</p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400">Total Open: </span>
          <span className="text-sm font-bold text-red-400">{exceptionData.open_exceptions ?? 0}</span>
        </div>
      </div>

      {/* Severity Bar Chart */}
      <div className="h-44 my-2">
        {hasData ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <XAxis
                dataKey="name"
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#64748b"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.75rem',
                  color: '#f8fafc',
                  fontSize: '12px',
                }}
                cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
              />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={SEVERITY_COLORS[entry.key?.toLowerCase()] || '#6366f1'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs">
            <span className="text-lg">🎉</span>
            <span className="mt-1">Zero active exceptions recorded</span>
          </div>
        )}
      </div>

      {/* Top Categories */}
      <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2">
        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Top Categories</span>
        <div className="grid grid-cols-2 gap-2">
          {categories.slice(0, 4).map((cat) => (
            <div
              key={cat.key}
              className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/50 text-xs"
            >
              <span className="text-slate-300 capitalize text-[11px] truncate">{cat.label || cat.key.replace(/_/g, ' ')}</span>
              <span className="font-semibold text-slate-200 ml-1">{cat.count}</span>
            </div>
          ))}
          {categories.length === 0 && (
            <div className="col-span-2 text-slate-500 text-xs text-center py-1">No category breakdown yet</div>
          )}
        </div>
      </div>
    </div>
  )
}
