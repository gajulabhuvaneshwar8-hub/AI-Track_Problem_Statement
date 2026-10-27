import React, { useState } from 'react'
import { FileText, Loader2, MessageSquarePlus, Send } from '../common/Icons'

export default function ReviewPanel({
  reviewerNote,
  status,
  onAddNote,
  disabled = false,
}) {
  const [newNote, setNewNote] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const isTerminal = status === 'resolved' || status === 'ignored'

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!newNote.trim()) return

    try {
      setIsSubmitting(true)
      setError(null)
      await onAddNote(newNote.trim())
      setNewNote('')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit review note.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-4 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-indigo-400" />
          <h4 className="text-xs font-semibold text-slate-200 tracking-wide uppercase">
            Human Investigation Notes
          </h4>
        </div>
        {status === 'open' && (
          <span className="text-[10px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
            Adding a note transitions status to Investigating
          </span>
        )}
      </div>

      {/* Existing Notes Log */}
      {reviewerNote ? (
        <div className="bg-slate-950/60 border border-slate-800/70 rounded-xl p-3 text-xs text-slate-300 font-sans whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
          {reviewerNote}
        </div>
      ) : (
        <div className="text-center py-4 text-xs text-slate-500 italic bg-slate-950/40 rounded-xl border border-slate-800/40">
          No reviewer notes added yet.
        </div>
      )}

      {/* Input Form */}
      {!isTerminal ? (
        <form onSubmit={handleSubmit} className="space-y-2">
          {error && (
            <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">
              {error}
            </div>
          )}
          <div className="relative">
            <textarea
              rows={3}
              disabled={disabled || isSubmitting}
              placeholder="Add findings, gateway inquiry results, or customer verification notes..."
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950/70 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/50 resize-none transition-all disabled:opacity-50"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={disabled || isSubmitting || !newNote.trim()}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
              <span>Add Review Note</span>
            </button>
          </div>
        </form>
      ) : (
        <div className="text-[11px] text-slate-500 italic bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/40 text-center">
          This exception is currently {status}. Reopen the ticket to append new review findings.
        </div>
      )}
    </div>
  )
}
