import React, { useState } from 'react'
import StatusBadge from '../common/StatusBadge'
import { formatDateTime } from '../../utils/formatters'

export default function EscalationCard({
  escalation = null,
  onEscalate = null,
  isEscalating = false,
}) {
  const [reason, setReason] = useState('')
  const [tier, setTier] = useState('Tier-2 Engineering')
  const [showForm, setShowForm] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!reason.trim()) return
    onEscalate?.({ reason, tier })
    setShowForm(false)
  }

  if (escalation) {
    return (
      <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-500/30">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-rose-400 text-base">⚠️</span>
            <h3 className="text-sm font-bold text-white tracking-wide">Escalation in Progress</h3>
          </div>
          <StatusBadge status="escalated" />
        </div>

        <div className="space-y-2.5 text-xs">
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/50 border border-slate-800">
            <span className="text-slate-400">Escalated Tier:</span>
            <span className="font-semibold text-rose-300">{escalation.escalated_to || escalation.tier || 'Operations Tier-2'}</span>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800">
            <span className="text-slate-400 block mb-1">Escalation Rationale:</span>
            <p className="text-slate-200">{escalation.reason || escalation.notes || 'Automated confidence threshold breached.'}</p>
          </div>

          {escalation.created_at && (
            <div className="text-[11px] text-slate-500 text-right">
              Escalated at: {formatDateTime(escalation.created_at)}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">Operations Escalation</h3>
          <p className="text-xs text-slate-400 mt-0.5">Route critical or uncertain cases to Tier-2 / Engineering</p>
        </div>
        {!showForm && onEscalate && (
          <button
            onClick={() => setShowForm(true)}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-colors"
          >
            Escalate Case
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mt-4 pt-4 border-t border-slate-800 space-y-3">
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Escalate To</label>
            <select
              value={tier}
              onChange={(e) => setTier(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="Tier-2 Operations">Tier-2 Financial Operations</option>
              <option value="Payment Engineering">Payment Gateway Engineering</option>
              <option value="Merchant Support">Merchant Success / Accounting</option>
              <option value="Compliance & Fraud">Compliance & Anti-Fraud Unit</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Reason / Notes</label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this exception requires manual operational intervention..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isEscalating}
              className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-500 text-white transition-colors disabled:opacity-50"
            >
              {isEscalating ? 'Escalating...' : 'Confirm Escalation'}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
