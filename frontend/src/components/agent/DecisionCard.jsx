import React from 'react'
import StatusBadge from '../common/StatusBadge'
import { formatPercent } from '../../utils/formatters'

export default function DecisionCard({ investigation }) {
  if (!investigation) return null

  const confidence = investigation.confidence_score !== null
    ? investigation.confidence_score * 100
    : 0

  return (
    <div className="p-6 rounded-2xl bg-gradient-to-br from-indigo-950/30 via-slate-900/60 to-slate-900/60 border border-indigo-500/20 shadow-lg shadow-black/30">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-slate-800">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400">
            Agent Triage Decision
          </span>
          <h3 className="text-lg font-bold text-white mt-0.5 capitalize">
            {investigation.decision ? investigation.decision.replace(/_/g, ' ') : 'Under Active Analysis'}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Action:</span>
          <StatusBadge status={investigation.recommended_action || 'pending'} />
        </div>
      </div>

      {/* Confidence score bar */}
      <div className="mb-5">
        <div className="flex items-center justify-between text-xs mb-1.5">
          <span className="text-slate-400 font-medium">Confidence Score</span>
          <span className="font-bold text-white">{formatPercent(confidence, 1)}</span>
        </div>
        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              confidence >= 80 ? 'bg-emerald-500' : confidence >= 50 ? 'bg-amber-500' : 'bg-rose-500'
            }`}
            style={{ width: `${Math.min(100, Math.max(0, confidence))}%` }}
          />
        </div>
      </div>

      {/* Root Cause & Reasoning */}
      <div className="space-y-3 text-xs">
        {investigation.root_cause && (
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-1">
              Identified Root Cause
            </span>
            <p className="text-slate-200 leading-relaxed font-medium">
              {investigation.root_cause}
            </p>
          </div>
        )}

        {investigation.reasoning && (
          <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/80">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-1">
              Agent Explanation & Rationale
            </span>
            <p className="text-slate-300 leading-relaxed">
              {investigation.reasoning}
            </p>
          </div>
        )}
      </div>

      {/* Financial safety disclaimer */}
      <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center gap-2 text-[11px] text-slate-400">
        <span className="text-indigo-400 text-sm">🔒</span>
        <span>
          <strong>Advisory Only:</strong> The AI Agent explains root causes and recommends actions. It does not alter financial ledgers or initiate fund transfers.
        </span>
      </div>
    </div>
  )
}
