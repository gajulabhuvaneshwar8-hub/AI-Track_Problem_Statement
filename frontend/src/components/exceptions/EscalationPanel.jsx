import React, { useState } from 'react'
import { AlertOctagon, Loader2, ShieldAlert } from '../common/Icons'

export default function EscalationPanel({
  exception,
  onEscalate,
  disabled = false,
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [reason, setReason] = useState('')
  const [suggestedTeam, setSuggestedTeam] = useState('Finance Operations')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const isEscalated = Boolean(exception.escalated_at)
  const isTerminal = exception.status === 'resolved' || exception.status === 'ignored'

  const handleEscalate = async () => {
    if (!reason.trim()) {
      setError('An escalation rationale is mandatory.')
      return
    }

    try {
      setIsSubmitting(true)
      setError(null)
      await onEscalate(reason.trim(), suggestedTeam)
      setIsOpen(false)
      setReason('')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to record escalation.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <h4 className="text-xs font-semibold text-slate-200 tracking-wide uppercase flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <span>Internal Escalation</span>
        </h4>
        {isEscalated && (
          <span className="text-[10px] font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full uppercase tracking-wider">
            Escalated Ticket
          </span>
        )}
      </div>

      {isEscalated ? (
        <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-3 text-xs space-y-1.5">
          <div className="flex items-center gap-2 font-semibold text-rose-300">
            <AlertOctagon className="w-4 h-4" />
            <span>Escalation Active</span>
          </div>
          {exception.escalation_reason && (
            <p className="text-slate-300 pl-6 leading-relaxed">
              {exception.escalation_reason}
            </p>
          )}
          {exception.escalated_at && (
            <div className="text-[11px] text-slate-400 pl-6">
              Escalated on {new Date(exception.escalated_at).toLocaleString()}
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-400">
            Discrepancy exceeds regular operator parameters? Flag internally for specialized review.
          </p>
          <button
            type="button"
            disabled={disabled || isTerminal}
            onClick={() => setIsOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-rose-600/90 hover:bg-rose-600 text-white text-xs font-medium shadow-md shadow-rose-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed shrink-0 ml-3"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Escalate Discrepancy</span>
          </button>
        </div>
      )}

      {/* Escalation Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 max-w-md w-full shadow-2xl shadow-black/80 space-y-4 animate-in zoom-in-95 duration-150">
            <div className="flex items-center gap-2.5">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              <h3 className="text-sm font-semibold text-slate-100">
                Internal Discrepancy Escalation
              </h3>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              This action creates an audit-grounded escalation record and routes the discrepancy on the Finance Operations dashboard. External emails or notifications will NOT be dispatched.
            </p>

            {error && (
              <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2.5">
                {error}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Target Team / Unit
                </label>
                <select
                  value={suggestedTeam}
                  onChange={(e) => setSuggestedTeam(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-rose-500 transition-colors"
                >
                  <option value="Finance Operations">Finance Operations</option>
                  <option value="Risk & Fraud Engineering">Risk & Fraud Engineering</option>
                  <option value="Banking Relations & Treasury">Banking Relations & Treasury</option>
                  <option value="Merchant Support & Escalations">Merchant Support & Escalations</option>
                  <option value="Core Engineering / Integrations">Core Engineering / Integrations</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Escalation Rationale *
                </label>
                <textarea
                  rows={3}
                  disabled={isSubmitting}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Document why this exception requires escalation..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                disabled={isSubmitting}
                onClick={() => setIsOpen(false)}
                className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmitting || !reason.trim()}
                onClick={handleEscalate}
                className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Confirm Escalation</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
