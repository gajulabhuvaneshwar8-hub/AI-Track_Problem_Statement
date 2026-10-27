import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import PageHeader from '../components/layout/PageHeader'
import DataTable from '../components/common/DataTable'
import StatusBadge from '../components/common/StatusBadge'
import Modal from '../components/common/Modal'
import {
  getMerchants,
  getReconciliationResults,
  getReconciliationSummary,
  runReconciliation,
} from '../services/reconciliationService'
import { formatCurrency, formatDateTime, formatPercent, truncateId } from '../utils/formatters'

const STATUS_FILTERS = [
  { value: '', label: 'All Match Statuses' },
  { value: 'matched', label: 'Matched' },
  { value: 'unmatched', label: 'Unmatched' },
  { value: 'amount_mismatch', label: 'Amount Mismatch' },
  { value: 'missing_in_bank', label: 'Missing in Bank' },
  { value: 'missing_in_gateway', label: 'Missing in Gateway' },
  { value: 'duplicate', label: 'Duplicate' },
  { value: 'unresolved', label: 'Unresolved' },
]

export default function Reconciliation() {
  const navigate = useNavigate()
  const [merchants, setMerchants] = useState([])
  const [selectedMerchant, setSelectedMerchant] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [summary, setSummary] = useState(null)
  const [results, setResults] = useState([])
  const [totalResults, setTotalResults] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(15)
  const [statusFilter, setStatusFilter] = useState('')
  const [loadingResults, setLoadingResults] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  // Detail Modal
  const [selectedResult, setSelectedResult] = useState(null)

  useEffect(() => {
    async function loadMerchants() {
      try {
        const data = await getMerchants()
        setMerchants(data.items || data || [])
      } catch (err) {
        console.error('Failed to load merchants:', err)
      }
    }
    loadMerchants()
  }, [])

  const fetchResults = async () => {
    setLoadingResults(true)
    setErrorMessage(null)
    try {
      const params = {
        page,
        page_size: pageSize,
      }
      if (selectedMerchant) params.merchant_id = selectedMerchant
      if (statusFilter) params.match_status = statusFilter

      const data = await getReconciliationResults(params)
      setResults(data.items || [])
      setTotalResults(data.total || 0)
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to load reconciliation results.')
    } finally {
      setLoadingResults(false)
    }
  }

  const fetchSummary = async () => {
    if (!selectedMerchant) return
    try {
      const data = await getReconciliationSummary(selectedMerchant)
      setSummary(data)
    } catch (err) {
      console.error('Failed to load summary:', err)
    }
  }

  useEffect(() => {
    fetchResults()
    fetchSummary()
  }, [selectedMerchant, statusFilter, page])

  const handleRunReconciliation = async () => {
    setIsRunning(true)
    setErrorMessage(null)
    setSuccessMessage(null)
    try {
      const resp = await runReconciliation(selectedMerchant || null)
      if (resp.summary) {
        setSummary(resp.summary)
      }
      setSuccessMessage(`Reconciliation engine run finished successfully. ${resp.matched_count || 0} matched, ${resp.unmatched_count || 0} exceptions.`)
      setPage(1)
      await fetchResults()
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to execute reconciliation.')
    } finally {
      setIsRunning(false)
    }
  }

  const columns = [
    {
      header: 'Match Status',
      accessor: 'match_status',
      render: (val) => <StatusBadge status={val} size="xs" />,
    },
    {
      header: 'Method',
      accessor: 'matching_method',
      render: (val) => <span className="font-mono text-slate-400 text-[11px]">{val || 'rule_based'}</span>,
    },
    {
      header: 'Confidence',
      accessor: 'confidence_score',
      render: (val) => (
        <span className="font-semibold text-slate-200">
          {val !== null && val !== undefined ? formatPercent(Number(val) * 100, 0) : '—'}
        </span>
      ),
    },
    {
      header: 'Expected (Gtwy)',
      accessor: 'expected_amount',
      className: 'text-right',
      render: (val) => <span className="font-mono text-slate-300">{formatCurrency(val)}</span>,
    },
    {
      header: 'Actual (Bank)',
      accessor: 'actual_amount',
      className: 'text-right',
      render: (val) => <span className="font-mono text-slate-300">{formatCurrency(val)}</span>,
    },
    {
      header: 'Difference',
      accessor: 'difference_amount',
      className: 'text-right',
      render: (val) => {
        const num = Number(val || 0)
        return (
          <span className={`font-mono font-semibold ${num === 0 ? 'text-slate-400' : 'text-amber-400'}`}>
            {formatCurrency(val)}
          </span>
        )
      },
    },
    {
      header: 'Reconciled At',
      accessor: 'reconciled_at',
      render: (val) => <span className="text-slate-400 text-[11px]">{formatDateTime(val)}</span>,
    },
    {
      header: 'Actions',
      accessor: 'id',
      className: 'text-right',
      render: (_, row) => (
        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => setSelectedResult(row)}
            className="px-2 py-1 text-[11px] rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            Inspect
          </button>
          <Link
            to={`/ai-analysis?reconciliation_id=${row.id}`}
            className="px-2 py-1 text-[11px] rounded bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 border border-indigo-500/30 transition-colors"
          >
            AI Insight
          </Link>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Deterministic Reconciliation Engine"
        subtitle="Single source of financial truth: exact rules-based matching across gateway ledgers and bank settlements"
        actions={
          <div className="flex items-center gap-3">
            <select
              value={selectedMerchant}
              onChange={(e) => {
                setSelectedMerchant(e.target.value)
                setPage(1)
              }}
              className="px-3 py-2 rounded-xl border border-slate-800 bg-slate-900 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Merchants (Platform-wide)</option>
              {merchants.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.business_name || m.name} ({m.email})
                </option>
              ))}
            </select>

            <button
              onClick={handleRunReconciliation}
              disabled={isRunning}
              className="px-4 py-2 rounded-xl font-semibold text-xs transition-all flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 text-white shadow-lg shadow-indigo-500/20 disabled:opacity-50"
            >
              <svg className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{isRunning ? 'Reconciling Engine...' : 'Run Reconciliation'}</span>
            </button>
          </div>
        }
      />

      {/* Notifications */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-center justify-between">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-red-400 hover:text-white">&times;</button>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center justify-between">
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 hover:text-white">&times;</button>
        </div>
      )}

      {/* Summary KPI grid if merchant summary available */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="text-[10px] uppercase font-bold text-slate-400">Total Txns</div>
            <div className="text-lg font-bold text-slate-100 mt-1">{summary.total_gateway_transactions}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-emerald-500/30">
            <div className="text-[10px] uppercase font-bold text-emerald-400">Matched</div>
            <div className="text-lg font-bold text-emerald-300 mt-1">{summary.matched}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-amber-500/30">
            <div className="text-[10px] uppercase font-bold text-amber-400">Diff</div>
            <div className="text-lg font-bold text-amber-300 mt-1">{summary.amount_mismatch}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-rose-500/30">
            <div className="text-[10px] uppercase font-bold text-rose-400">Missing Bank</div>
            <div className="text-lg font-bold text-rose-300 mt-1">{summary.missing_in_bank}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-purple-500/30">
            <div className="text-[10px] uppercase font-bold text-purple-400">Missing Gtwy</div>
            <div className="text-lg font-bold text-purple-300 mt-1">{summary.missing_in_gateway}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-sky-500/30">
            <div className="text-[10px] uppercase font-bold text-sky-400">Duplicates</div>
            <div className="text-lg font-bold text-sky-300 mt-1">{summary.duplicates}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-orange-500/30">
            <div className="text-[10px] uppercase font-bold text-orange-400">Unresolved</div>
            <div className="text-lg font-bold text-orange-300 mt-1">{summary.unresolved}</div>
          </div>
          <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/40">
            <div className="text-[10px] uppercase font-bold text-indigo-400">Match Rate</div>
            <div className="text-lg font-bold text-indigo-200 mt-1">{summary.reconciliation_accuracy}%</div>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-3">
          <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Filter By Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value)
              setPage(1)
            }}
            className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {STATUS_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </div>

        <button
          onClick={fetchResults}
          className="text-xs px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 transition-colors"
        >
          Refresh Results
        </button>
      </div>

      {/* Results Table */}
      <DataTable
        columns={columns}
        data={results}
        loading={loadingResults}
        onRowClick={(row) => setSelectedResult(row)}
        pagination={{
          page,
          pageSize,
          total: totalResults,
          onPageChange: (p) => setPage(p),
        }}
        emptyTitle="No Reconciliation Results"
        emptyMessage="Run reconciliation to generate automated match records."
      />

      {/* Inspect Modal */}
      <Modal
        isOpen={Boolean(selectedResult)}
        onClose={() => setSelectedResult(null)}
        title="Reconciliation Match Detail"
        subtitle={`ID: ${selectedResult?.id}`}
        footer={
          <div className="flex items-center justify-between w-full">
            <Link
              to={`/ai-analysis?reconciliation_id=${selectedResult?.id}`}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white"
            >
              Analyze with AI
            </Link>
            <button
              onClick={() => setSelectedResult(null)}
              className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200"
            >
              Close
            </button>
          </div>
        }
      >
        {selectedResult && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div>
                <span className="text-slate-400 block mb-1">Match Status</span>
                <StatusBadge status={selectedResult.match_status} />
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Confidence</span>
                <span className="font-bold text-white">
                  {selectedResult.confidence_score !== null ? formatPercent(Number(selectedResult.confidence_score) * 100) : '—'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Expected Amount</span>
                <span className="font-mono text-slate-200">{formatCurrency(selectedResult.expected_amount)}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Actual Amount</span>
                <span className="font-mono text-slate-200">{formatCurrency(selectedResult.actual_amount)}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Difference Amount</span>
                <span className="font-mono text-amber-400 font-bold">{formatCurrency(selectedResult.difference_amount)}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Matching Method</span>
                <span className="font-mono text-slate-300">{selectedResult.matching_method || 'rule_based'}</span>
              </div>
            </div>

            {selectedResult.explanation && (
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400 font-semibold block mb-1">Engine Explanation</span>
                <p className="text-slate-200 leading-relaxed">{selectedResult.explanation}</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
