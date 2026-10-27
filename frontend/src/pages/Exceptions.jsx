import React, { useState, useEffect, useCallback } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  Clock,
  Filter,
  Layers,
  RefreshCw,
  Scale,
  ShieldAlert,
  UserCheck,
  Users,
} from '../components/common/Icons'
import PageHeader from '../components/layout/PageHeader'
import exceptionService from '../services/exceptionService'
import ExceptionFilters from '../components/exceptions/ExceptionFilters'
import ExceptionTable from '../components/exceptions/ExceptionTable'
import ExceptionDetails from '../components/exceptions/ExceptionDetails'

export default function Exceptions() {
  const [exceptions, setExceptions] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [assignees, setAssignees] = useState([])
  const [summary, setSummary] = useState(null)
  const [selectedExceptionId, setSelectedExceptionId] = useState(null)

  // Filters
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 20,
    search: '',
    status: '',
    severity: '',
    category: '',
    assigned_to: '',
  })

  // Known categories for filter dropdown
  const categories = [
    'amount_mismatch',
    'missing_in_bank',
    'missing_in_gateway',
    'timing_difference',
    'fee_discrepancy',
    'currency_mismatch',
    'duplicate_transaction',
  ]

  // Load assignable team members
  const fetchAssignees = async () => {
    try {
      const data = await exceptionService.listAssignees()
      setAssignees(data || [])
    } catch (err) {
      console.error('Failed to load assignees:', err)
    }
  }

  // Load aggregated workflow summary
  const fetchSummary = async () => {
    try {
      const data = await exceptionService.getWorkflowSummary()
      setSummary(data)
    } catch (err) {
      console.error('Failed to load workflow summary:', err)
    }
  }

  // Fetch paginated exceptions
  const fetchExceptions = useCallback(async () => {
    try {
      setLoading(true)
      const params = {
        page: filters.page,
        page_size: filters.pageSize,
      }
      if (filters.search) params.search = filters.search
      if (filters.status) params.status = filters.status
      if (filters.severity) params.severity = filters.severity
      if (filters.category) params.category = filters.category
      if (filters.assigned_to) params.assigned_to = filters.assigned_to

      const res = await exceptionService.listExceptions(params)
      setExceptions(res.items || [])
      setTotal(res.total || 0)
    } catch (err) {
      console.error('Failed to load exceptions:', err)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    fetchAssignees()
    fetchSummary()
  }, [])

  useEffect(() => {
    fetchExceptions()
  }, [fetchExceptions])

  const handleResetFilters = () => {
    setFilters({
      page: 1,
      pageSize: 20,
      search: '',
      status: '',
      severity: '',
      category: '',
      assigned_to: '',
    })
  }

  const handleInlineAssign = async (exceptionId, userId) => {
    try {
      const updated = await exceptionService.assignException(exceptionId, userId)
      setExceptions((prev) =>
        prev.map((e) =>
          e.id === exceptionId
            ? {
                ...e,
                assigned_to: updated.assigned_to,
                assignee_name: updated.assignee_name,
              }
            : e
        )
      )
      fetchSummary()
    } catch (err) {
      console.error('Failed inline assign:', err)
    }
  }

  const handleTicketUpdated = (updatedExc) => {
    setExceptions((prev) =>
      prev.map((e) => (e.id === updatedExc.id ? { ...e, ...updatedExc } : e))
    )
    fetchSummary()
  }

  // Filter shortcut helpers from summary cards
  const applyQuickFilter = (newStatus) => {
    setFilters((prev) => ({
      ...prev,
      page: 1,
      status: prev.status === newStatus ? '' : newStatus,
    }))
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <PageHeader
        title="Exception Management & Human-in-the-Loop"
        subtitle="Operational workbench for reviewing discrepancies, inspecting AI diagnoses, managing team assignments, and executing grounded workflow resolutions."
      >
        <button
          type="button"
          onClick={() => {
            fetchSummary()
            fetchExceptions()
          }}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 text-xs font-medium transition-all shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-indigo-400 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Records</span>
        </button>
      </PageHeader>

      {/* Workflow Summary Strip */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Total */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-3.5 backdrop-blur-md">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Total Exceptions</span>
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="text-xl font-bold text-slate-100 font-mono">
              {summary.total}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Across all ledgers</div>
          </div>

          {/* Open */}
          <div
            onClick={() => applyQuickFilter('open')}
            className={`cursor-pointer rounded-2xl p-3.5 border transition-all ${
              filters.status === 'open'
                ? 'bg-red-500/20 border-red-500/50 shadow-lg shadow-red-500/10'
                : 'bg-slate-900/60 border-slate-800/80 hover:border-red-500/30'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">Open Tickets</span>
              <AlertCircle className="w-3.5 h-3.5 text-red-400" />
            </div>
            <div className="text-xl font-bold text-red-400 font-mono">
              {summary.open}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Awaiting triage</div>
          </div>

          {/* Investigating */}
          <div
            onClick={() => applyQuickFilter('investigating')}
            className={`cursor-pointer rounded-2xl p-3.5 border transition-all ${
              filters.status === 'investigating'
                ? 'bg-cyan-500/20 border-cyan-500/50 shadow-lg shadow-cyan-500/10'
                : 'bg-slate-900/60 border-slate-800/80 hover:border-cyan-500/30'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">Investigating</span>
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-xl font-bold text-cyan-400 font-mono">
              {summary.investigating}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">In active review</div>
          </div>

          {/* Unassigned */}
          <div
            onClick={() =>
              setFilters((prev) => ({
                ...prev,
                page: 1,
                assigned_to: prev.assigned_to === 'unassigned' ? '' : 'unassigned',
              }))
            }
            className={`cursor-pointer rounded-2xl p-3.5 border transition-all ${
              filters.assigned_to === 'unassigned'
                ? 'bg-indigo-500/20 border-indigo-500/50 shadow-lg shadow-indigo-500/10'
                : 'bg-slate-900/60 border-slate-800/80 hover:border-indigo-500/30'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">Unassigned</span>
              <Users className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="text-xl font-bold text-indigo-400 font-mono">
              {summary.unassigned}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Needs operator</div>
          </div>

          {/* Resolved Today */}
          <div
            onClick={() => applyQuickFilter('resolved')}
            className={`cursor-pointer rounded-2xl p-3.5 border transition-all ${
              filters.status === 'resolved'
                ? 'bg-emerald-500/20 border-emerald-500/50 shadow-lg shadow-emerald-500/10'
                : 'bg-slate-900/60 border-slate-800/80 hover:border-emerald-500/30'
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">Resolved Today</span>
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-xl font-bold text-emerald-400 font-mono">
              {summary.resolved_today}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Closed discrepancies</div>
          </div>

          {/* Escalated & Critical */}
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-3.5 backdrop-blur-md">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">Escalated</span>
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            </div>
            <div className="text-xl font-bold text-rose-400 font-mono">
              {summary.escalated}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">
              {summary.critical} Critical Severity
            </div>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <ExceptionFilters
        filters={filters}
        onChange={setFilters}
        onReset={handleResetFilters}
        assignees={assignees}
        categories={categories}
      />

      {/* Table Section */}
      <ExceptionTable
        exceptions={exceptions}
        total={total}
        page={filters.page}
        pageSize={filters.pageSize}
        onPageChange={(newPage) => setFilters((prev) => ({ ...prev, page: newPage }))}
        onSelectException={(id) => setSelectedExceptionId(id)}
        onAssignException={handleInlineAssign}
        assignees={assignees}
        isLoading={loading}
      />

      {/* 360-Degree Detail Drawer */}
      {selectedExceptionId && (
        <ExceptionDetails
          exceptionId={selectedExceptionId}
          onClose={() => setSelectedExceptionId(null)}
          onUpdate={handleTicketUpdated}
          assignees={assignees}
        />
      )}
    </div>
  )
}
