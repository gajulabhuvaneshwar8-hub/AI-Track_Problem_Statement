/**
 * AgentInvestigation.jsx
 * Autonomous AI Reconciliation Investigation Agent Workbench.
 * Integrates directly with AppLayout, PageHeader, and deep links from Dashboard & Exceptions.
 */

import React, { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import PageHeader from '../components/layout/PageHeader'
import StatusBadge from '../components/common/StatusBadge'
import {
  getEscalation,
  getInvestigationEvidence,
  investigateException,
  investigateReconciliation,
  listInvestigations,
} from '../services/agentService'
import { formatPercent, formatDateTime, truncateId } from '../utils/formatters'

const DECISION_STYLES = {
  monitor: {
    badge: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/50',
    icon: '🟢',
    title: 'MONITOR',
    desc: 'Low severity or self-correcting delay. Keep under automated surveillance.',
  },
  review: {
    badge: 'bg-amber-950/80 text-amber-300 border-amber-500/50',
    icon: '🟡',
    title: 'REVIEW',
    desc: 'Discrepancy warrants human inspection during standard operations queue.',
  },
  escalate: {
    badge: 'bg-rose-950/80 text-rose-300 border-rose-500/50',
    icon: '🔴',
    title: 'ESCALATE',
    desc: 'Critical risk or large discrepancy. Immediate escalation to specialized team.',
  },
}

const RISK_BADGES = {
  critical: 'bg-rose-950 text-rose-300 border-rose-700/60',
  high: 'bg-orange-950 text-orange-300 border-orange-700/60',
  medium: 'bg-amber-950 text-amber-300 border-amber-700/60',
  low: 'bg-emerald-950 text-emerald-300 border-emerald-700/60',
}

const STAGES = [
  { id: 1, name: 'Trigger Received', desc: 'Exception/Recon event dispatched' },
  { id: 2, name: 'Evidence Aggregation', desc: 'Multi-ledger signals collected' },
  { id: 3, name: 'Deterministic Engine', desc: 'Deterministic financial rules' },
  { id: 4, name: 'AI Synthesis', desc: 'Explanations & confirmed facts' },
  { id: 5, name: 'Escalation & Audit', desc: 'Team routing & immutable logs' },
]

export default function AgentInvestigation() {
  const [searchParams] = useSearchParams()
  const exceptionParam = searchParams.get('exception_id') || searchParams.get('exceptionId')
  const reconParam = searchParams.get('reconciliation_id') || searchParams.get('reconciliationId')
  const investigationParam = searchParams.get('investigation_id') || searchParams.get('investigationId')

  // State
  const [investigations, setInvestigations] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [investigating, setInvestigating] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  // Selected investigation
  const [selectedInv, setSelectedInv] = useState(null)
  const [evidenceList, setEvidenceList] = useState([])
  const [escalationData, setEscalationData] = useState(null)
  const [activeTab, setActiveTab] = useState('summary') // 'summary' | 'evidence' | 'escalation'

  // Trigger form
  const [triggerType, setTriggerType] = useState('exception') // 'exception' | 'reconciliation'
  const [targetId, setTargetId] = useState(exceptionParam || reconParam || '')
  const [forceReevaluate, setForceReevaluate] = useState(false)

  // Filters
  const [filterDecision, setFilterDecision] = useState('')
  const [filterRisk, setFilterRisk] = useState('')
  const [filterType, setFilterType] = useState('')

  useEffect(() => {
    fetchInvestigations()
  }, [page, filterDecision, filterRisk, filterType])

  useEffect(() => {
    if (exceptionParam) {
      setTriggerType('exception')
      setTargetId(exceptionParam)
    } else if (reconParam) {
      setTriggerType('reconciliation')
      setTargetId(reconParam)
    }
  }, [exceptionParam, reconParam])

  const fetchInvestigations = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: 10 }
      if (filterDecision) params.decision = filterDecision
      if (filterRisk) params.risk_level = filterRisk
      if (filterType) params.investigation_type = filterType

      const data = await listInvestigations(params)
      setInvestigations(data.items || [])
      setTotal(data.total || 0)

      if (investigationParam && data.items) {
        const found = data.items.find((i) => i.id === investigationParam)
        if (found) {
          loadInvestigationDetails(found)
          return
        }
      }

      if (data.items && data.items.length > 0 && !selectedInv) {
        loadInvestigationDetails(data.items[0])
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to load investigations.')
    } finally {
      setLoading(false)
    }
  }

  const loadInvestigationDetails = async (inv) => {
    setSelectedInv(inv)
    setEvidenceList(inv.evidence || [])
    setEscalationData(null)

    try {
      const [evData, escData] = await Promise.allSettled([
        getInvestigationEvidence(inv.id),
        inv.escalation_required ? getEscalation(inv.id) : Promise.resolve(null),
      ])
      if (evData.status === 'fulfilled') setEvidenceList(evData.value)
      if (escData.status === 'fulfilled' && escData.value) setEscalationData(escData.value)
    } catch (err) {
      console.error('Failed loading extra details:', err)
    }
  }

  const handleRunInvestigation = async (e) => {
    e?.preventDefault()
    if (!targetId.trim()) {
      setErrorMessage('Please enter an Exception ID or Reconciliation ID.')
      return
    }

    setInvestigating(true)
    setErrorMessage(null)
    setSuccessMessage(null)

    try {
      let res
      if (triggerType === 'exception') {
        res = await investigateException(targetId.trim(), forceReevaluate)
      } else {
        res = await investigateReconciliation(targetId.trim(), forceReevaluate)
      }

      setSuccessMessage(`Investigation completed with decision: ${res.decision.toUpperCase()}`)
      loadInvestigationDetails(res)
      await fetchInvestigations()
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Investigation execution failed.')
    } finally {
      setInvestigating(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Reconciliation Investigation Agent"
        subtitle="Multi-ledger evidence aggregation, deterministic rules, explainable synthesis, and operations escalation"
        badge={
          <span className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Agent Ready
          </span>
        }
      />

      {/* Notifications */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-950/70 border border-rose-700/80 text-rose-200 text-xs flex items-center justify-between">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white">&times;</button>
        </div>
      )}
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-950/70 border border-emerald-700/80 text-emerald-200 text-xs flex items-center justify-between">
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 hover:text-white">&times;</button>
        </div>
      )}

      {/* 5-Stage Pipeline Progress Strip */}
      <section className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Autonomous Agent Lifecycle Pipeline
          </span>
          <span className="text-xs text-indigo-400 font-mono">
            Deterministic Truth · Read-Only Guardrails
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {STAGES.map((s) => (
            <div
              key={s.id}
              className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 transition hover:border-indigo-500/40"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="w-5 h-5 rounded-full bg-indigo-600/30 border border-indigo-400 text-indigo-300 text-[10px] font-bold flex items-center justify-center">
                  {s.id}
                </span>
                <span className="text-xs font-semibold text-slate-200">{s.name}</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-tight">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Trigger Card */}
      <section className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">🎯</span>
            <h2 className="text-xs font-bold text-white tracking-wide uppercase">
              Dispatch Agent Investigation
            </h2>
          </div>
          <span className="text-xs text-slate-400">
            Select exception or reconciliation ID to gather evidence & generate triage verdict
          </span>
        </div>

        <form onSubmit={handleRunInvestigation} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          <div className="md:col-span-3 space-y-1.5">
            <label className="text-xs font-medium text-slate-300">Entity Type</label>
            <select
              value={triggerType}
              onChange={(e) => setTriggerType(e.target.value)}
              className="w-full text-xs px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="exception">Payment Exception ID</option>
              <option value="reconciliation">Reconciliation Result ID</option>
            </select>
          </div>

          <div className="md:col-span-6 space-y-1.5">
            <label className="text-xs font-medium text-slate-300">Target UUID Reference</label>
            <input
              type="text"
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              placeholder="e.g. 8fa19e34-5f40-410a-b516-ec85..."
              className="w-full text-xs px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>

          <div className="md:col-span-3 flex items-center gap-3">
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={forceReevaluate}
                onChange={(e) => setForceReevaluate(e.target.checked)}
                className="rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-0"
              />
              Force Re-run
            </label>

            <button
              type="submit"
              disabled={investigating}
              className="flex-1 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
            >
              {investigating ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <span>⚡</span> Investigate
                </>
              )}
            </button>
          </div>
        </form>
      </section>

      {/* Main Grid: Left = Investigations History / Right = Active Workbench */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: History & Filters (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <span>📂</span> Prior Investigations ({total})
              </h3>
              <button
                onClick={fetchInvestigations}
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                ↻ Refresh
              </button>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-3 gap-2">
              <select
                value={filterDecision}
                onChange={(e) => setFilterDecision(e.target.value)}
                className="text-[11px] px-2 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300 focus:outline-none"
              >
                <option value="">All Decisions</option>
                <option value="monitor">MONITOR</option>
                <option value="review">REVIEW</option>
                <option value="escalate">ESCALATE</option>
              </select>

              <select
                value={filterRisk}
                onChange={(e) => setFilterRisk(e.target.value)}
                className="text-[11px] px-2 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300 focus:outline-none"
              >
                <option value="">All Risks</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>

              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="text-[11px] px-2 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300 focus:outline-none"
              >
                <option value="">All Types</option>
                <option value="amount_mismatch">Amount Mismatch</option>
                <option value="missing_in_bank">Missing in Bank</option>
                <option value="missing_in_gateway">Missing in Gateway</option>
                <option value="duplicate">Duplicate</option>
                <option value="unresolved">Unresolved</option>
              </select>
            </div>

            {/* Investigations List */}
            <div className="space-y-2 max-h-[560px] overflow-y-auto pr-1">
              {loading ? (
                <div className="py-12 text-center text-xs text-slate-400">Loading records...</div>
              ) : investigations.length === 0 ? (
                <div className="py-12 text-center text-xs text-slate-500">
                  No agent investigations recorded yet. Trigger one above!
                </div>
              ) : (
                investigations.map((inv) => {
                  const isSelected = selectedInv?.id === inv.id
                  const decisionMeta = DECISION_STYLES[inv.decision] || DECISION_STYLES.review
                  return (
                    <div
                      key={inv.id}
                      onClick={() => loadInvestigationDetails(inv)}
                      className={`p-3 rounded-xl border transition cursor-pointer ${
                        isSelected
                          ? 'bg-indigo-950/40 border-indigo-500/80 shadow-md'
                          : 'bg-slate-950/50 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${decisionMeta.badge}`}
                        >
                          {decisionMeta.icon} {decisionMeta.title}
                        </span>
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border ${
                            RISK_BADGES[inv.risk_level] || RISK_BADGES.medium
                          }`}
                        >
                          {inv.risk_level?.toUpperCase()}
                        </span>
                      </div>

                      <div className="text-xs font-semibold text-slate-200 truncate mt-1 capitalize">
                        {inv.investigation_type?.replace(/_/g, ' ')}
                      </div>
                      <p className="text-[11px] text-slate-400 line-clamp-2 mt-0.5">
                        {inv.summary}
                      </p>

                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/80 text-[10px] text-slate-400">
                        <span className="font-mono">
                          {inv.completed_at ? formatDateTime(inv.completed_at) : 'Pending'}
                        </span>
                        <span>Confidence: {inv.confidence_score !== null ? formatPercent(Number(inv.confidence_score) * 100, 0) : '—'}</span>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Active Workbench & Evidence Explorer (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {selectedInv ? (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-sm space-y-5">
              {/* Investigation Top Meta */}
              <div className="flex flex-wrap items-start justify-between gap-3 pb-4 border-b border-slate-800">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-indigo-400">
                      ID: {truncateId(selectedInv.id)}
                    </span>
                    <StatusBadge status={selectedInv.status} size="xs" />
                  </div>
                  <h3 className="text-lg font-bold text-white mt-1 capitalize">
                    {selectedInv.investigation_type?.replace(/_/g, ' ')}
                  </h3>
                </div>

                {/* Decision Highlight Badge */}
                {(() => {
                  const decMeta = DECISION_STYLES[selectedInv.decision] || DECISION_STYLES.review
                  return (
                    <div className={`px-4 py-2 rounded-xl border text-center ${decMeta.badge}`}>
                      <div className="text-xs font-bold tracking-wider flex items-center gap-1.5 justify-center">
                        <span>{decMeta.icon}</span>
                        <span>VERDICT: {decMeta.title}</span>
                      </div>
                      <div className="text-[10px] opacity-80 mt-0.5">
                        Confidence: {selectedInv.confidence_score !== null ? formatPercent(Number(selectedInv.confidence_score) * 100, 1) : '—'}
                      </div>
                    </div>
                  )
                })()}
              </div>

              {/* Tabs */}
              <div className="flex border-b border-slate-800 text-xs font-semibold gap-4">
                <button
                  onClick={() => setActiveTab('summary')}
                  className={`pb-2 transition ${
                    activeTab === 'summary'
                      ? 'text-indigo-400 border-b-2 border-indigo-500'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Synthesis & Facts
                </button>
                <button
                  onClick={() => setActiveTab('evidence')}
                  className={`pb-2 transition flex items-center gap-1.5 ${
                    activeTab === 'evidence'
                      ? 'text-indigo-400 border-b-2 border-indigo-500'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Evidence Ledger ({evidenceList.length})
                </button>
                {selectedInv.escalation_required && (
                  <button
                    onClick={() => setActiveTab('escalation')}
                    className={`pb-2 transition flex items-center gap-1 ${
                      activeTab === 'escalation'
                        ? 'text-rose-400 border-b-2 border-rose-500'
                        : 'text-rose-400/70 hover:text-rose-300'
                    }`}
                  >
                    🚨 Escalation Details
                  </button>
                )}
              </div>

              {/* Tab 1: Synthesis & Grounded Facts */}
              {activeTab === 'summary' && (
                <div className="space-y-4">
                  {/* Summary Card */}
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                    <div className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                      <span>📝</span> Executive Summary
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed">
                      {selectedInv.summary}
                    </p>
                  </div>

                  {/* Grounded Facts vs Possible Causes */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                      <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                        <span>🔒</span> Confirmed Facts
                      </div>
                      {selectedInv.confirmed_facts && selectedInv.confirmed_facts.length > 0 ? (
                        <ul className="space-y-1.5 text-xs text-slate-300">
                          {selectedInv.confirmed_facts.map((fact, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <span className="text-emerald-500">✓</span>
                              <span className="leading-snug">{fact}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-slate-500 italic">No explicit facts recorded.</p>
                      )}
                    </div>

                    <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                      <div className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                        <span>🔍</span> Hypotheses (Unconfirmed)
                      </div>
                      {selectedInv.possible_causes && selectedInv.possible_causes.length > 0 ? (
                        <ul className="space-y-1.5 text-xs text-slate-300">
                          {selectedInv.possible_causes.map((cause, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <span className="text-amber-500">?</span>
                              <span className="leading-snug">{cause}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-slate-500 italic">No alternative hypotheses identified.</p>
                      )}
                    </div>
                  </div>

                  {/* Recommended Action */}
                  {selectedInv.recommended_action && (
                    <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-800/60 space-y-1.5">
                      <div className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                        <span>💡</span> Recommended Action
                      </div>
                      <p className="text-xs text-slate-200 leading-relaxed">
                        {selectedInv.recommended_action}
                      </p>
                    </div>
                  )}

                  {/* Financial Safety Guardrail Notice */}
                  <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 flex items-center justify-between text-xs text-slate-400">
                    <div>
                      <span>Financial Ledger Truth: </span>
                      <strong className="text-white">Immutable (Read-Only)</strong>
                    </div>
                    <span className="text-[11px] text-indigo-400">
                      Mode: {selectedInv.impact?.ai_synthesized ? 'LLM Enhanced' : 'Deterministic Rule Engine'}
                    </span>
                  </div>
                </div>
              )}

              {/* Tab 2: Evidence Ledger */}
              {activeTab === 'evidence' && (
                <div className="space-y-3">
                  <div className="overflow-x-auto rounded-xl border border-slate-800">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="bg-slate-950 text-slate-400 uppercase text-[10px]">
                        <tr>
                          <th className="p-2.5">Source</th>
                          <th className="p-2.5">Field</th>
                          <th className="p-2.5">Recorded Value</th>
                          <th className="p-2.5 text-right">Reliability</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                        {evidenceList.map((ev, i) => (
                          <tr key={i} className="hover:bg-slate-900/40">
                            <td className="p-2.5">
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-indigo-300 border border-slate-700">
                                {ev.source}
                              </span>
                            </td>
                            <td className="p-2.5 font-medium text-white">{ev.field}</td>
                            <td className="p-2.5 font-mono text-[11px] text-slate-300 max-w-xs truncate">
                              {typeof ev.value === 'object' ? JSON.stringify(ev.value) : String(ev.value)}
                            </td>
                            <td className="p-2.5 text-right font-mono text-emerald-400">
                              {ev.reliability ? `${(ev.reliability * 100).toFixed(0)}%` : '100%'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Tab 3: Escalation */}
              {activeTab === 'escalation' && (
                <div className="p-5 rounded-xl bg-rose-950/30 border border-rose-800/60 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">🚨</span>
                      <div>
                        <h4 className="text-sm font-bold text-rose-200">
                          Escalation Assigned: {selectedInv.escalation_team}
                        </h4>
                        <p className="text-xs text-rose-300/80">
                          Automated routing determined by risk severity and discrepancy type
                        </p>
                      </div>
                    </div>
                    <span className="text-xs px-2.5 py-1 rounded-full bg-rose-900/80 text-rose-200 font-bold border border-rose-600">
                      {escalationData?.priority || 'HIGH'} PRIORITY
                    </span>
                  </div>

                  {escalationData && (
                    <div className="space-y-2 pt-2 border-t border-rose-900/40 text-xs text-slate-200">
                      <div>
                        <strong className="text-rose-300">Escalation Reason: </strong>
                        <span>{escalationData.reason}</span>
                      </div>
                      <div>
                        <strong className="text-rose-300">Required Action: </strong>
                        <span>{escalationData.suggested_action}</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-slate-500">
              <span className="text-3xl block mb-2">🔎</span>
              <p className="text-xs">Select an investigation on the left or dispatch a new one above.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
