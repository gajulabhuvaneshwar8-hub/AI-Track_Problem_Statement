import React from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { formatPercent } from '../../utils/formatters'
import StatusBadge from '../common/StatusBadge'

const COLORS = {
  Matched: '#10b981',           // Emerald
  Unmatched: '#f43f5e',         // Rose/Red
  'Partially Matched': '#f59e0b', // Amber
  'Manual Review': '#a855f7',   // Purple
}

export default function ReconciliationHealth({ health, onActionClick }) {
  if (!health) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-center h-64 text-xs text-slate-500">
        Reconciliation data not available
      </div>
    )
  }

  const rawData = [
    { name: 'Matched', value: health.matched_count || 0, color: COLORS.Matched },
    { name: 'Unmatched', value: health.unmatched_count || 0, color: COLORS.Unmatched },
    { name: 'Partially Matched', value: health.partially_matched_count || 0, color: COLORS['Partially Matched'] },
    { name: 'Manual Review', value: health.manual_review_count || 0, color: COLORS['Manual Review'] },
  ]

  const chartData = rawData.filter((d) => d.value > 0)
  const hasData = chartData.length > 0

  return (
    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">Reconciliation Health</h3>
          <p className="text-xs text-slate-400 mt-0.5">Automated 2-way & 3-way match efficiency</p>
        </div>
        <StatusBadge status={health.status} label={health.status} />
      </div>

      <div className="relative h-48 my-2 flex items-center justify-center">
        {hasData ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={4}
                stroke="#0f172a"
                strokeWidth={3}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.75rem',
                  color: '#f8fafc',
                  fontSize: '12px',
                  boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
                }}
                itemStyle={{ color: '#e2e8f0' }}
              />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex flex-col items-center justify-center text-slate-500 text-xs">
            <span className="text-lg">📊</span>
            <span>No reconciliation runs recorded yet</span>
          </div>
        )}

        {/* Center rate KPI */}
        {hasData && (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-2xl font-black text-white tracking-tight">
              {formatPercent(health.match_rate, 1)}
            </span>
            <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400">Match Rate</span>
          </div>
        )}
      </div>

      {/* Legend Breakdown */}
      <div className="grid grid-cols-2 gap-2 mt-3 pt-4 border-t border-slate-800/80 text-xs">
        {rawData.map((item) => (
          <div key={item.name} className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/50">
            <div className="flex items-center gap-1.5 min-w-0">
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
              <span className="text-slate-400 truncate text-[11px]">{item.name}</span>
            </div>
            <span className="font-semibold text-slate-200 shrink-0 text-xs">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
