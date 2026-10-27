import React from 'react'
import StatusBadge from '../common/StatusBadge'

const STAGES = [
  { id: 'detection', label: '1. Detection', desc: 'Exception identified during reconciliation' },
  { id: 'evidence', label: '2. Evidence Collection', desc: 'Queries gateway logs, ledger, and bank feeds' },
  { id: 'analysis', label: '3. Root Cause Analysis', desc: 'Deterministic heuristics & AI correlation' },
  { id: 'decision', label: '4. Decision Formulation', desc: 'Confidence scoring & action recommendation' },
  { id: 'resolution', label: '5. Action / Escalation', desc: 'Workflow resolution or escalation to ops' },
]

export default function InvestigationTimeline({ investigation }) {
  if (!investigation) return null

  // Determine stage progress based on investigation status and decision
  const isCompleted = investigation.status === 'completed' || investigation.status === 'resolved'
  const isEscalated = investigation.status === 'escalated'

  const getStageStatus = (index) => {
    if (isCompleted || isEscalated) return 'completed'
    if (investigation.status === 'investigating') {
      if (index <= 1) return 'completed'
      if (index === 2) return 'active'
      return 'pending'
    }
    if (index === 0) return 'completed'
    return 'pending'
  }

  return (
    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">Investigation Lifecycle Timeline</h3>
          <p className="text-xs text-slate-400 mt-0.5">Automated multi-stage investigation progress</p>
        </div>
        <StatusBadge status={investigation.status} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
        {STAGES.map((stage, idx) => {
          const status = getStageStatus(idx)
          const isCurrent = status === 'active'
          const isDone = status === 'completed'

          return (
            <div
              key={stage.id}
              className={`p-4 rounded-xl border flex flex-col justify-between transition-all ${
                isDone
                  ? 'bg-slate-950/60 border-emerald-500/30'
                  : isCurrent
                  ? 'bg-indigo-950/20 border-indigo-500/50 shadow-lg shadow-indigo-500/10'
                  : 'bg-slate-950/20 border-slate-800/60 opacity-60'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      isDone
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : isCurrent
                        ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/40 animate-pulse'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {isDone ? '✓' : idx + 1}
                  </span>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                    {isDone ? 'Done' : isCurrent ? 'In Progress' : 'Queued'}
                  </span>
                </div>
                <h4 className="text-xs font-semibold text-slate-200">{stage.label}</h4>
                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{stage.desc}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
