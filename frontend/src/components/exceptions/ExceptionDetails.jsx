import React, { useEffect, useState } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bot,
  Building2,
  Calendar,
  CheckCircle,
  CreditCard,
  ExternalLink,
  FileText,
  History,
  Info,
  Loader2,
  RefreshCw,
  Scale,
  ShieldAlert,
  Sparkles,
  User,
  X,
} from '../common/Icons'
import exceptionService from '../../services/exceptionService'
import SeverityBadge from './SeverityBadge'
import ExceptionStatusBadge from './ExceptionStatusBadge'
import AssignmentControl from './AssignmentControl'
import ReviewPanel from './ReviewPanel'
import ResolutionPanel from './ResolutionPanel'
import EscalationPanel from './EscalationPanel'
import ExceptionTimeline from './ExceptionTimeline'

export default function ExceptionDetails({
  exceptionId,
  onClose,
  onUpdate,
  assignees = [],
}) {
  const [activeTab, setActiveTab] = useState('overview') // 'overview' | 'ai' | 'timeline'
  const [details, setDetails] = useState(null)
  const [timeline, setTimeline] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchFullContext = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const [detailsData, timelineData] = await Promise.all([
        exceptionService.getExceptionDetails(exceptionId),
        exceptionService.getExceptionTimeline(exceptionId),
      ])
      setDetails(detailsData)
      setTimeline(timelineData?.events || [])
    } catch (err) {
      console.error('Error fetching exception context:', err)
      setError(err?.response?.data?.detail || 'Failed to load exception details.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (exceptionId) {
      fetchFullContext()
    }
  }, [exceptionId])

  const handleAssign = async (userId) => {
    const updated = await exceptionService.assignException(exceptionId, userId)
    setDetails((prev) => ({
      ...prev,
      exception: {
        ...prev.exception,
        assigned_to: updated.assigned_to,
        assignee_name: updated.assignee_name,
      },
      assignee: assignees.find((u) => u.id === userId) || null,
    }))
    if (onUpdate) onUpdate(updated)
    // Refresh timeline in background
    exceptionService.getExceptionTimeline(exceptionId).then((t) => setTimeline(t?.events || []))
  }

  const handleAddReviewNote = async (note) => {
    const updated = await exceptionService.addReviewNote(exceptionId, note)
    setDetails((prev) => ({
      ...prev,
      exception: {
        ...prev.exception,
        status: updated.status,
        reviewer_note: updated.reviewer_note,
      },
    }))
    if (onUpdate) onUpdate(updated)
    const t = await exceptionService.getExceptionTimeline(exceptionId)
    setTimeline(t?.events || [])
  }

  const handleResolve = async (resolutionNote) => {
    const updated = await exceptionService.resolveException(exceptionId, resolutionNote)
    setDetails((prev) => ({
      ...prev,
      exception: {
        ...prev.exception,
        status: updated.status,
        resolution_note: updated.resolution_note,
        resolved_at: updated.resolved_at,
        resolved_by: updated.resolved_by,
      },
    }))
    if (onUpdate) onUpdate(updated)
    const t = await exceptionService.getExceptionTimeline(exceptionId)
    setTimeline(t?.events || [])
  }

  const handleIgnore = async (reason) => {
    const updated = await exceptionService.ignoreException(exceptionId, reason)
    setDetails((prev) => ({
      ...prev,
      exception: {
        ...prev.exception,
        status: updated.status,
        resolution_note: updated.resolution_note,
        ignored_at: updated.ignored_at,
        ignored_by: updated.ignored_by,
      },
    }))
    if (onUpdate) onUpdate(updated)
    const t = await exceptionService.getExceptionTimeline(exceptionId)
    setTimeline(t?.events || [])
  }

  const handleEscalate = async (reason, suggestedTeam) => {
    const updated = await exceptionService.escalateException(exceptionId, reason, suggestedTeam)
    setDetails((prev) => ({
      ...prev,
      exception: {
        ...prev.exception,
        status: updated.status,
        escalation_reason: updated.escalation_reason,
        escalated_at: updated.escalated_at,
      },
    }))
    if (onUpdate) onUpdate(updated)
    const t = await exceptionService.getExceptionTimeline(exceptionId)
    setTimeline(t?.events || [])
  }

  const handleReopen = async (reason) => {
    const updated = await exceptionService.reopenException(exceptionId, reason)
    setDetails((prev) => ({
      ...prev,
      exception: {
        ...prev.exception,
        status: updated.status,
        reviewer_note: updated.reviewer_note,
        resolved_at: null,
        resolved_by: null,
        ignored_at: null,
        ignored_by: null,
      },
    }))
    if (onUpdate) onUpdate(updated)
    const t = await exceptionService.getExceptionTimeline(exceptionId)
    setTimeline(t?.events || [])
  }

  const exc = details?.exception

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-4xl bg-slate-950 border-l border-slate-800 h-full flex flex-col shadow-2xl shadow-black animate-in slide-in-from-right duration-200">
        {/* Top Header */}
        <div className="p-5 border-b border-slate-800/80 bg-slate-900/60 flex items-start justify-between gap-4">
          <div className="space-y-1.5 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-mono text-indigo-400 font-semibold bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded">
                EXP-{exceptionId.slice(0, 8).toUpperCase()}
              </span>
              {exc && (
                <>
                  <SeverityBadge severity={exc.severity} />
                  <ExceptionStatusBadge status={exc.status} />
                  {exc.category && (
                    <span className="text-xs text-slate-400 bg-slate-800 px-2.5 py-0.5 rounded-full border border-slate-700">
                      {exc.category.replace(/_/g, ' ')}
                    </span>
                  )}
                </>
              )}
            </div>
            <h2 className="text-base font-bold text-slate-100 truncate">
              {exc?.title || 'Exception Ticket'}
            </h2>
            {exc?.description && (
              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                {exc.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={fetchFullContext}
              title="Refresh ticket data"
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Strip */}
        <div className="flex items-center gap-1 px-5 border-b border-slate-800 bg-slate-900/30 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('overview')}
            className={`py-3 px-4 font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'overview'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Scale className="w-4 h-4" />
            <span>Overview & Evidence</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('ai')}
            className={`py-3 px-4 font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'ai'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-4 h-4 text-violet-400" />
            <span>AI Intelligence & Agent</span>
            {(details?.ai_analysis || details?.agent_investigation) && (
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
            )}
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('timeline')}
            className={`py-3 px-4 font-medium border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'timeline'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <History className="w-4 h-4 text-cyan-400" />
            <span>Grounded Audit Timeline</span>
            <span className="text-[10px] px-1.5 py-0.2 bg-slate-800 text-slate-400 rounded-full font-mono">
              {timeline.length}
            </span>
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {isLoading ? (
            <div className="h-64 flex flex-col items-center justify-center gap-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
              <span className="text-xs">Loading complete exception evidence...</span>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
              {error}
            </div>
          ) : !exc ? (
            <div className="text-center text-xs text-slate-500 py-10">
              Exception not found.
            </div>
          ) : (
            <>
              {/* ============================================================ */}
              {/* TAB 1: OVERVIEW & EVIDENCE */}
              {/* ============================================================ */}
              {activeTab === 'overview' && (
                <div className="space-y-5">
                  {/* Top quick stats cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                      <div className="text-[11px] text-slate-400 mb-1">Discrepancy Amount</div>
                      <div className="text-base font-bold text-slate-100 font-mono">
                        {exc.amount !== null && exc.amount !== undefined ? (
                          <>
                            <span className="text-xs text-indigo-400 font-normal mr-1">{exc.currency || 'INR'}</span>
                            {Number(exc.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          </>
                        ) : (
                          'N/A'
                        )}
                      </div>
                    </div>

                    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                      <div className="text-[11px] text-slate-400 mb-1">Assignee</div>
                      <div className="mt-0.5">
                        <AssignmentControl
                          currentAssigneeId={exc.assigned_to}
                          currentAssigneeName={exc.assignee_name}
                          assignees={assignees}
                          onAssign={handleAssign}
                          size="sm"
                        />
                      </div>
                    </div>

                    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                      <div className="text-[11px] text-slate-400 mb-1">Created At</div>
                      <div className="text-xs font-medium text-slate-200 font-mono mt-1">
                        {new Date(exc.created_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </div>

                    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3">
                      <div className="text-[11px] text-slate-400 mb-1">Recon Decision</div>
                      <div className="text-xs font-semibold text-amber-400 uppercase tracking-wide mt-1">
                        {details.reconciliation?.match_status || 'Mismatched'}
                      </div>
                    </div>
                  </div>

                  {/* Side-by-side Evidence Card */}
                  <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                      <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wide flex items-center gap-2">
                        <Scale className="w-4 h-4 text-indigo-400" />
                        <span>Reconciliation Evidence Comparison</span>
                      </h4>
                      {details.reconciliation && (
                        <span className="text-[11px] font-mono text-slate-400">
                          Diff:{' '}
                          <strong className="text-rose-400">
                            {details.reconciliation.difference_amount !== null
                              ? `${details.reconciliation.difference_amount} ${exc.currency}`
                              : 'N/A'}
                          </strong>
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Internal Gateway Side */}
                      <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 space-y-2.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-400">
                            <CreditCard className="w-3.5 h-3.5" />
                            <span>Internal Gateway Ledger</span>
                          </div>
                          {details.transaction && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono uppercase">
                              {details.transaction.status}
                            </span>
                          )}
                        </div>

                        {details.transaction ? (
                          <div className="space-y-1.5 text-xs">
                            <div className="flex justify-between py-1 border-b border-slate-900">
                              <span className="text-slate-500">Ref ID:</span>
                              <span className="font-mono text-slate-200">{details.transaction.reference_id}</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-slate-900">
                              <span className="text-slate-500">Amount:</span>
                              <span className="font-mono font-bold text-slate-100">
                                {details.transaction.currency} {Number(details.transaction.amount).toFixed(2)}
                              </span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-slate-900">
                              <span className="text-slate-500">Payment Method:</span>
                              <span className="text-slate-300 capitalize">{details.transaction.payment_method || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between py-1">
                              <span className="text-slate-500">Recorded:</span>
                              <span className="text-slate-400 font-mono text-[11px]">
                                {new Date(details.transaction.created_at).toLocaleString()}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="py-6 text-center text-xs text-slate-500 italic">
                            No matching internal gateway record found (Unmatched in Bank).
                          </div>
                        )}
                      </div>

                      {/* Bank Statement Side */}
                      <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 space-y-2.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                            <Building2 className="w-3.5 h-3.5" />
                            <span>Bank Statement Entry</span>
                          </div>
                          {details.bank_transaction && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono uppercase">
                              {details.bank_transaction.status || 'Posted'}
                            </span>
                          )}
                        </div>

                        {details.bank_transaction ? (
                          <div className="space-y-1.5 text-xs">
                            <div className="flex justify-between py-1 border-b border-slate-900">
                              <span className="text-slate-500">Bank Ref:</span>
                              <span className="font-mono text-slate-200">{details.bank_transaction.bank_reference}</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-slate-900">
                              <span className="text-slate-500">Statement Amount:</span>
                              <span className="font-mono font-bold text-slate-100">
                                {details.bank_transaction.currency || exc.currency} {Number(details.bank_transaction.amount).toFixed(2)}
                              </span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-slate-900">
                              <span className="text-slate-500">Bank Name:</span>
                              <span className="text-slate-300">{details.bank_transaction.bank || 'Primary Clearing Bank'}</span>
                            </div>
                            <div className="flex justify-between py-1">
                              <span className="text-slate-500">Transaction Date:</span>
                              <span className="text-slate-400 font-mono text-[11px]">
                                {details.bank_transaction.transaction_date
                                  ? new Date(details.bank_transaction.transaction_date).toLocaleString()
                                  : 'N/A'}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div className="py-6 text-center text-xs text-slate-500 italic">
                            No matching bank transaction statement received (Missing in Bank).
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Human Investigation Notes */}
                  <ReviewPanel
                    reviewerNote={exc.reviewer_note}
                    status={exc.status}
                    onAddNote={handleAddReviewNote}
                  />

                  {/* Resolution Controls */}
                  <ResolutionPanel
                    exception={exc}
                    onResolve={handleResolve}
                    onIgnore={handleIgnore}
                    onReopen={handleReopen}
                  />

                  {/* Internal Escalation Controls */}
                  <EscalationPanel
                    exception={exc}
                    onEscalate={handleEscalate}
                  />
                </div>
              )}

              {/* ============================================================ */}
              {/* TAB 2: AI INTELLIGENCE & AGENT */}
              {/* ============================================================ */}
              {activeTab === 'ai' && (
                <div className="space-y-5">
                  {/* AI Analysis Summary */}
                  {details.ai_analysis ? (
                    <div className="bg-slate-900/80 border border-violet-500/20 rounded-xl p-4 space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-violet-400" />
                          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wide">
                            AI Discrepancy Diagnostics
                          </h4>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-slate-400">Confidence:</span>
                          <span className="text-xs font-bold font-mono text-violet-300">
                            {Math.round((details.ai_analysis.confidence_score || 0) * 100)}%
                          </span>
                        </div>
                      </div>

                      <div className="space-y-2 text-xs">
                        <div>
                          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                            Diagnosed Root Cause
                          </div>
                          <p className="text-slate-200 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 leading-relaxed">
                            {details.ai_analysis.root_cause || details.ai_analysis.summary}
                          </p>
                        </div>

                        {details.ai_analysis.recommended_action && (
                          <div>
                            <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider mb-1">
                              AI Recommendation
                            </div>
                            <p className="text-slate-300 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 leading-relaxed">
                              {details.ai_analysis.recommended_action}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="p-6 text-center text-xs text-slate-500 italic bg-slate-900/40 rounded-xl border border-slate-800/60">
                      No standalone AI discrepancy analysis recorded for this transaction.
                    </div>
                  )}

                  {/* Autonomous Agent Investigation */}
                  {details.agent_investigation ? (
                    <div className="bg-slate-900/80 border border-cyan-500/20 rounded-xl p-4 space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                        <div className="flex items-center gap-2">
                          <Bot className="w-4 h-4 text-cyan-400" />
                          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wide">
                            Autonomous Agent Investigation
                          </h4>
                        </div>
                        <span className="text-xs font-mono font-bold text-cyan-400 uppercase bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded-full">
                          Decision: {details.agent_investigation.decision}
                        </span>
                      </div>

                      <div className="space-y-3 text-xs">
                        <div>
                          <span className="text-slate-400 font-medium">Summary: </span>
                          <span className="text-slate-200">{details.agent_investigation.summary}</span>
                        </div>

                        {details.agent_investigation.confirmed_facts?.length > 0 && (
                          <div>
                            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                              Confirmed Evidence Facts
                            </div>
                            <ul className="space-y-1 pl-4 list-disc text-slate-300 text-xs">
                              {details.agent_investigation.confirmed_facts.map((fact, i) => (
                                <li key={i}>{fact}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {details.agent_investigation.recommended_action && (
                          <div className="bg-cyan-500/10 border border-cyan-500/20 p-2.5 rounded-lg text-cyan-300">
                            <strong>Recommended Action:</strong> {details.agent_investigation.recommended_action}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="p-6 text-center text-xs text-slate-500 italic bg-slate-900/40 rounded-xl border border-slate-800/60">
                      No autonomous agent investigation conducted for this ticket.
                    </div>
                  )}

                  {/* AI vs Human Role Note */}
                  <div className="p-3 bg-slate-950/40 border border-slate-800/60 rounded-xl text-xs text-slate-400 flex items-start gap-2.5">
                    <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                    <span>
                      The AI agent performs automated discovery, root cause inference, and recommendation generation. The final decision to resolve, ignore, or escalate remains strictly under the authority of a human finance operator.
                    </span>
                  </div>
                </div>
              )}

              {/* ============================================================ */}
              {/* TAB 3: AUDIT TIMELINE */}
              {/* ============================================================ */}
              {activeTab === 'timeline' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                    <div>
                      <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wide">
                        Audit Trail & Event Log
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        Strictly grounded timeline derived directly from immutable database audit records.
                      </p>
                    </div>
                  </div>

                  <ExceptionTimeline events={timeline} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
