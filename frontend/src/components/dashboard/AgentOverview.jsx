import React from 'react'
import { Link } from 'react-router-dom'
import StatusBadge from '../common/StatusBadge'

export default function AgentOverview({ investigationData }) {
  if (!investigationData) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-center h-64 text-xs text-slate-500">
        AI agent metrics not available
      </div>
    )
  }

  const actions = investigationData.by_recommended_action || []

  return (
    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center font-bold text-xs">
            🤖
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">AI Agent Triage</h3>
            <p className="text-xs text-slate-400">Autonomous investigation & escalation</p>
          </div>
        </div>
        <Link
          to="/agent"
          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
        >
          <span>Open Agent</span>
          <span>&rarr;</span>
        </Link>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3 my-2">
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
          <p className="text-[11px] font-medium text-slate-400">Total Runs</p>
          <p className="text-xl font-bold text-white mt-1">{investigationData.total_investigations || 0}</p>
        </div>
        <div className="p-3 rounded-xl bg-slate-950/60 border border-emerald-500/20 text-center">
          <p className="text-[11px] font-medium text-emerald-400">Resolved</p>
          <p className="text-xl font-bold text-emerald-300 mt-1">{investigationData.resolved_count || 0}</p>
        </div>
        <div className="p-3 rounded-xl bg-slate-950/60 border border-rose-500/20 text-center">
          <p className="text-[11px] font-medium text-rose-400">Escalated</p>
          <p className="text-xl font-bold text-rose-300 mt-1">{investigationData.escalated_count || 0}</p>
        </div>
      </div>

      {/* Recommended actions breakdown */}
      <div className="mt-3 pt-3 border-t border-slate-800/80">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
            Recommended Actions
          </span>
          <span className="text-[11px] text-slate-400">
            Avg Time: <strong className="text-slate-200">{investigationData.avg_resolution_time_seconds || 1.2}s</strong>
          </span>
        </div>

        <div className="space-y-1.5 max-h-32 overflow-y-auto">
          {actions.map((act) => (
            <div
              key={act.key}
              className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-slate-950/40 border border-slate-800/40 text-xs"
            >
              <StatusBadge status={act.key} label={act.label} size="xs" />
              <span className="font-semibold text-slate-200">{act.count}</span>
            </div>
          ))}
          {actions.length === 0 && (
            <div className="text-slate-500 text-xs text-center py-2">No agent actions recorded yet</div>
          )}
        </div>
      </div>
    </div>
  )
}
