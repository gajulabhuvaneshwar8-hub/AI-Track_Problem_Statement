/**
 * AIAnalysis.jsx
 * AI Mismatch Analysis & Diagnostic Insights.
 * Explains reconciliation anomalies, root causes, financial impact, and next actions
 * while preserving deterministic reconciliation results as financial truth.
 */

import React, { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import PageHeader from '../components/layout/PageHeader'
import StatusBadge from '../components/common/StatusBadge'
import DataTable from '../components/common/DataTable'
import {
  analyzeException,
  analyzeReconciliation,
  investigateException,
  listAnalyses,
} from '../services/aiAnalysisService'
import { formatDateTime, formatPercent, truncateId } from '../utils/formatters'

export default function AIAnalysis() {
  const [searchParams] = useSearchParams()
  const reconciliationIdParam = searchParams.get('reconciliation_id')
  const exceptionIdParam = searchParams.get('exception_id')

  const [analyses, setAnalyses] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [selectedAnalysis, setSelectedAnalysis] = useState(null)
  const [investigationData, setInvestigationData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [riskFilter, setRiskFilter] = useState('')

  useEffect(() => {
    fetchAnalyses()
  }, [page, statusFilter, riskFilter])

  useEffect(() => {
    if (reconciliationIdParam) {
      handleAnalyzeReconciliation(reconciliationIdParam, false)
    } else if (exceptionIdParam) {
      handleAnalyzeException(exceptionIdParam, false)
    }
  }, [reconciliationIdParam, exceptionIdParam])

  const fetchAnalyses = async () => {
    setLoading(true)
    try {
      const params = { page, page_size: 10 }
      if (statusFilter) params.status = statusFilter
      if (riskFilter) params.risk_level = riskFilter

      const data = await listAnalyses(params)
      setAnalyses(data.items || [])
      setTotal(data.total || 0)

      if (data.items && data.items.length > 0 && !selectedAnalysis) {
        setSelectedAnalysis(data.items[0])
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to load AI analysis history.')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeReconciliation = async (reconId, force = false) => {
    setAnalyzing(true)
    setErrorMessage(null)
    setInvestigationData(null)
    try {
      const res = await analyzeReconciliation(reconId, force)
      setSelectedAnalysis(res)
      await fetchAnalyses()
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to analyze reconciliation result.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleAnalyzeException = async (excId, force = false) => {
    setAnalyzing(true)
    setErrorMessage(null)
    setInvestigationData(null)
    try {
      const res = await analyzeException(excId, force)
      setSelectedAnalysis(res)
      await fetchAnalyses()
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to analyze exception.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleDeepInvestigate = async () => {
    if (!selectedAnalysis?.exception_id) {
      setErrorMessage('Deep investigation requires an associated exception ticket.')
      return
    }
    setAnalyzing(true)
    setErrorMessage(null)
    try {
      const inv = await investigateException(selectedAnalysis.exception_id, true)
      setInvestigationData(inv)
      setSelectedAnalysis(inv.analysis)
      await fetchAnalyses()
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Deep investigation failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  const columns = [
    {
      header: 'Type',
      accessor: 'analysis_type',
      render: (val) => <span className="font-semibold text-slate-200 capitalize">{val ? val.replace(/_/g, ' ') : '—'}</span>,
    },
    {
      header: 'Risk Level',
      accessor: 'risk_level',
      render: (val) => <StatusBadge status={val} size="xs" />,
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (val) => <StatusBadge status={val} size="xs" />,
    },
    {
      header: 'Confidence',
      accessor: 'confidence_score',
      render: (val) => (
        <span className="font-semibold text-slate-200">
          {val ? formatPercent(Number(val) * 100, 0) : '—'}
        </span>
      ),
    },
    {
      header: 'Summary',
      accessor: 'summary',
      render: (val) => <span className="text-slate-300 max-w-xs truncate block">{val}</span>,
    },
    {
      header: 'Provider',
      accessor: 'ai_provider',
      render: (val) => <span className="font-mono text-slate-400 text-[11px]">{val}</span>,
    },
    {
      header: 'Timestamp',
      accessor: 'created_at',
      render: (val) => <span className="text-slate-400 text-[11px]">{formatDateTime(val)}</span>,
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Mismatch Analysis"
        subtitle="LLM-assisted root cause analysis, financial impact evaluation, and recommended next actions"
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (selectedAnalysis?.reconciliation_id) {
                  handleAnalyzeReconciliation(selectedAnalysis.reconciliation_id, true)
                } else if (selectedAnalysis?.exception_id) {
                  handleAnalyzeException(selectedAnalysis.exception_id, true)
                }
              }}
              disabled={analyzing || !selectedAnalysis}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-200 disabled:opacity-40 transition-colors"
            >
              {analyzing ? 'Analyzing...' : 'Force Re-analyze'}
            </button>
            <button
              onClick={handleDeepInvestigate}
              disabled={analyzing || !selectedAnalysis?.exception_id}
              className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 transition-colors"
            >
              Deep Investigation
            </button>
          </div>
        }
      />

      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 text-xs flex items-center justify-between">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-red-400 hover:text-white">&times;</button>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Total Analyses</span>
          <div className="text-2xl font-bold text-white mt-1">{total}</div>
          <span className="text-[10px] text-slate-500">Historical records</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Risk Assessments</span>
          <div className="text-2xl font-bold text-orange-400 mt-1">
            {analyses.filter((a) => a.risk_level === 'critical' || a.risk_level === 'high').length} High
          </div>
          <span className="text-[10px] text-slate-500">Urgent operational attention</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Fallback Ratio</span>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {analyses.filter((a) => a.status === 'fallback').length}
          </div>
          <span className="text-[10px] text-slate-500">Deterministic fallback runs</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Financial Authority</span>
          <div className="text-sm font-bold text-emerald-400 mt-2 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            Deterministic Engine
          </div>
          <span className="text-[10px] text-slate-500">AI advisory only</span>
        </div>
      </div>

      {/* Selected Analysis View */}
      {selectedAnalysis && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
          {selectedAnalysis.status === 'fallback' && (
            <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-800/60 text-amber-200 text-xs flex items-center gap-2 font-medium">
              <span>⚠️</span>
              <span>AI provider unavailable — rule-based fallback analysis active. Financial ledger remains authoritative.</span>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <StatusBadge status={selectedAnalysis.risk_level} label={`Risk: ${selectedAnalysis.risk_level}`} />
                <span className="px-2 py-0.5 rounded text-[11px] bg-slate-800 text-slate-300 font-mono">
                  Score: {selectedAnalysis.confidence_score ? formatPercent(Number(selectedAnalysis.confidence_score) * 100, 0) : '—'}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  {selectedAnalysis.ai_provider} ({selectedAnalysis.model_name})
                </span>
              </div>
              <div className="text-[11px] text-slate-500">
                Analysis ID: <span className="font-mono text-slate-400">{truncateId(selectedAnalysis.id)}</span> • Created:{' '}
                {formatDateTime(selectedAnalysis.created_at)}
              </div>
            </div>

            {selectedAnalysis.reconciliation_id && (
              <Link
                to={`/reconciliation`}
                className="text-indigo-400 hover:text-indigo-300 text-xs font-semibold"
              >
                Inspect Match in Reconciliation &rarr;
              </Link>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-1">Executive Summary</h3>
              <p className="text-xs text-slate-200 leading-relaxed">{selectedAnalysis.summary}</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-1">Root-Cause Analysis</h3>
              <p className="text-xs text-slate-300 leading-relaxed">{selectedAnalysis.root_cause || 'No specific root cause identified.'}</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-1">Financial & Operational Impact</h3>
              <p className="text-xs text-slate-300 leading-relaxed">{selectedAnalysis.impact || 'Standard variance within tolerance.'}</p>
            </div>

            <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-900/40">
              <h3 className="text-xs uppercase font-bold text-indigo-300 tracking-wider mb-1">Recommended Action</h3>
              <p className="text-xs text-indigo-100 leading-relaxed">{selectedAnalysis.recommended_action || 'Proceed with standard operational review.'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Historical Analyses Table */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-white">AI Analysis History (Audit Trail)</h2>

          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-200"
            >
              <option value="">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="fallback">Fallback</option>
            </select>

            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="text-xs px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-200"
            >
              <option value="">All Risks</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={analyses}
          loading={loading}
          onRowClick={(row) => setSelectedAnalysis(row)}
          pagination={{
            page,
            pageSize: 10,
            total,
            onPageChange: (p) => setPage(p),
          }}
          emptyTitle="No AI Analysis History"
          emptyMessage="Select any reconciliation match or exception to request automated AI explanation."
        />
      </div>
    </div>
  )
}
