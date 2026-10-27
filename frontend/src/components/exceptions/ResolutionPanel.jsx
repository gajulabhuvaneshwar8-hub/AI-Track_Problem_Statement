import React, { useState } from 'react'
import {
  AlertTriangle,
  CheckCircle,
  EyeOff,
  Info,
  Loader2,
  RotateCcw,
  ShieldAlert,
} from '../common/Icons'

export default function ResolutionPanel({
  exception,
  onResolve,
  onIgnore,
  onReopen,
  disabled = false,
}) {
  const [activeModal, setActiveModal] = useState(null) // 'resolve' | 'ignore' | 'reopen'
  const [noteText, setNoteText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const isResolved = exception.status === 'resolved'
  const isIgnored = exception.status === 'ignored'
  const isTerminal = isResolved || isIgnored

  const openModal = (type) => {
    setActiveModal(type)
    setNoteText('')
    setError(null)
  }

  const closeModal = () => {
    if (isSubmitting) return
    setActiveModal(null)
    setNoteText('')
    setError(null)
  }

  const handleConfirm = async () => {
    if (!noteText.trim()) {
      setError('A rationale note is mandatory for this action.')
      return
    }

    try {
      setIsSubmitting(true)
      setError(null)
      if (activeModal === 'resolve') {
        await onResolve(noteText.trim())
      } else if (activeModal === 'ignore') {
        await onIgnore(noteText.trim())
      } else if (activeModal === 'reopen') {
        await onReopen(noteText.trim())
      }
      closeModal()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Operation failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <h4 className="text-xs font-semibold text-slate-200 tracking-wide uppercase flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-400" />
          <span>Ticket Workflow Decision</span>
        </h4>
        <span className="text-[11px] text-slate-400 font-mono">
          Current: <strong className="text-slate-200 uppercase">{exception.status}</strong>
        </span>
      </div>

      {/* Resolution / Ignore info if already resolved */}
      {isResolved && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 text-xs space-y-1">
          <div className="flex items-center gap-2 font-medium text-emerald-300">
            <CheckCircle className="w-4 h-4" />
            <span>Ticket Marked as Resolved</span>
          </div>
          {exception.resolution_note && (
            <p className="text-slate-300 pl-6 text-xs">{exception.resolution_note}</p>
          )}
          {exception.resolved_at && (
            <div className="text-[11px] text-slate-400 pl-6">
              Resolved on {new Date(exception.resolved_at).toLocaleString()}
            </div>
          )}
        </div>
      )}

      {isIgnored && (
        <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3 text-xs space-y-1">
          <div className="flex items-center gap-2 font-medium text-slate-300">
            <EyeOff className="w-4 h-4 text-slate-400" />
            <span>Ticket Marked as Ignored / Accepted Variance</span>
          </div>
          {exception.resolution_note && (
            <p className="text-slate-300 pl-6 text-xs">{exception.resolution_note}</p>
          )}
          {exception.ignored_at && (
            <div className="text-[11px] text-slate-400 pl-6">
              Ignored on {new Date(exception.ignored_at).toLocaleString()}
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        {!isTerminal ? (
          <>
            <button
              type="button"
              disabled={disabled}
              onClick={() => openModal('resolve')}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Resolve Exception</span>
            </button>

            <button
              type="button"
              disabled={disabled}
              onClick={() => openModal('ignore')}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all disabled:opacity-50"
            >
              <EyeOff className="w-3.5 h-3.5 text-slate-400" />
              <span>Ignore Discrepancy</span>
            </button>
          </>
        ) : (
          <button
            type="button"
            disabled={disabled}
            onClick={() => openModal('reopen')}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium shadow-md shadow-amber-600/20 transition-all disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reopen Ticket for Investigation</span>
          </button>
        )}
      </div>

      {/* Financial Guardrail Alert */}
      <div className="flex items-start gap-2 p-2.5 bg-slate-950/40 border border-slate-800/40 rounded-lg text-[11px] text-slate-400">
        <Info className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
        <span>
          <strong>Financial Guardrail:</strong> Human resolution decisions update ticket workflow status and audit records. Reconciliation determinations and ledger balances are strictly preserved.
        </span>
      </div>

      {/* Action Modal */}
      {activeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 max-w-md w-full shadow-2xl shadow-black/80 space-y-4 animate-in zoom-in-95 duration-150">
            <div className="flex items-center gap-2.5">
              {activeModal === 'resolve' && <CheckCircle className="w-5 h-5 text-emerald-400" />}
              {activeModal === 'ignore' && <EyeOff className="w-5 h-5 text-slate-400" />}
              {activeModal === 'reopen' && <RotateCcw className="w-5 h-5 text-amber-400" />}
              <h3 className="text-sm font-semibold text-slate-100">
                {activeModal === 'resolve' && 'Confirm Exception Resolution'}
                {activeModal === 'ignore' && 'Mark Exception as Ignored'}
                {activeModal === 'reopen' && 'Reopen Exception for Investigation'}
              </h3>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              {activeModal === 'resolve' &&
                'Document the operational rationale for resolving this discrepancy (e.g., fee adjustment acknowledged, settlement verified).'}
              {activeModal === 'ignore' &&
                'Document why this discrepancy can be safely ignored (e.g., agreed threshold variance, testing artifact).'}
              {activeModal === 'reopen' &&
                'Explain why this previously closed ticket is being reopened for ongoing investigation.'}
            </p>

            {error && (
              <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2.5">
                {error}
              </div>
            )}

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                {activeModal === 'resolve' ? 'Resolution Rationale *' : 'Mandatory Explanation *'}
              </label>
              <textarea
                rows={3}
                disabled={isSubmitting}
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Enter mandatory review rationale..."
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                disabled={isSubmitting}
                onClick={closeModal}
                className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSubmitting || !noteText.trim()}
                onClick={handleConfirm}
                className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                  activeModal === 'resolve'
                    ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20'
                    : activeModal === 'ignore'
                    ? 'bg-slate-700 hover:bg-slate-600 shadow-slate-700/20'
                    : 'bg-amber-600 hover:bg-amber-500 shadow-amber-600/20'
                }`}
              >
                {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>
                  {activeModal === 'resolve'
                    ? 'Confirm Resolution'
                    : activeModal === 'ignore'
                    ? 'Confirm Ignore'
                    : 'Confirm Reopen'}
                </span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
