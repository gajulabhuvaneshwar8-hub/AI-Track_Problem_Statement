import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bot,
  CheckCircle,
  Clock,
  ExternalLink,
  Layers,
  RefreshCw,
  Scale,
  ShieldAlert,
  Users,
} from '../components/common/Icons'
import PageHeader from '../components/layout/PageHeader'
import KPICard from '../components/dashboard/KPICard'
import ReconciliationHealth from '../components/dashboard/ReconciliationHealth'
import ExceptionOverview from '../components/dashboard/ExceptionOverview'
import AgentOverview from '../components/dashboard/AgentOverview'
import RecentExceptions from '../components/dashboard/RecentExceptions'
import RecentInvestigations from '../components/dashboard/RecentInvestigations'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorState from '../components/common/ErrorState'
import { dashboardService } from '../services/dashboardService'
import { reconciliationService } from '../services/reconciliationService'
import { exceptionService } from '../services/exceptionService'
import { formatCurrency, formatPercent } from '../utils/formatters'

export default function Dashboard() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [summary, setSummary] = useState(null)
  const [health, setHealth] = useState(null)
  const [exceptionsData, setExceptionsData] = useState(null)
  const [investigationsData, setInvestigationsData] = useState(null)
  const [workflowSummary, setWorkflowSummary] = useState(null)

  // Reconciliation run trigger
  const [runningRecon, setRunningRecon] = useState(false)
  const [reconMessage, setReconMessage] = useState(null)

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [sum, hlt, exc, inv, wf] = await Promise.all([
        dashboardService.getSummary(),
        dashboardService.getReconciliationHealth(),
        dashboardService.getExceptions(),
        dashboardService.getInvestigations(),
        exceptionService.getWorkflowSummary().catch(() => null),
      ])
      setSummary(sum)
      setHealth(hlt)
      setExceptionsData(exc)
      setInvestigationsData(inv)
      setWorkflowSummary(wf)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load dashboard metrics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const handleRunReconciliation = async () => {
    try {
      setRunningRecon(true)
      setReconMessage(null)
      const res = await reconciliationService.runReconciliation()
      setReconMessage(`Reconciliation completed: ${res.matched_count || 0} matched, ${res.unmatched_count || 0} unmatched.`)
      // Refresh dashboard
      await fetchDashboardData()
    } catch (err) {
      setReconMessage(`Failed: ${err.response?.data?.detail || err.message}`)
    } finally {
      setRunningRecon(false)
    }
  }

  if (loading && !summary) {
    return <LoadingSpinner message="Assembling Finance Operations Control Center..." className="h-96" />
  }

  if (error && !summary) {
    return <ErrorState title="Dashboard Offline" message={error} onRetry={fetchDashboardData} className="mt-8" />
  }

  return (
    <div className="space-y-6">
      {/* Top Banner / Notification if recon run */}
      {reconMessage && (
        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-between text-xs text-indigo-200">
          <span>{reconMessage}</span>
          <button onClick={() => setReconMessage(null)} className="text-indigo-400 hover:text-white">&times;</button>
        </div>
      )}

      {/* Page Header */}
      <PageHeader
        title="Finance Operations Control Center"
        subtitle="Real-time automated payment reconciliation, multi-rail exceptions, and AI agent triage"
        actions={
          <>
            <button
              onClick={() => fetchDashboardData()}
              disabled={loading}
              className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-indigo-400 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>

            <button
              onClick={() => navigate('/import')}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors border border-slate-700"
            >
              <span>Import Data</span>
            </button>

            <button
              onClick={handleRunReconciliation}
              disabled={runningRecon}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${runningRecon ? 'animate-spin' : ''}`} />
              <span>{runningRecon ? 'Reconciling...' : 'Run Reconciliation'}</span>
            </button>
          </>
        }
      />

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Gross Volume"
          value={formatCurrency(summary?.total_volume, summary?.currency || 'INR')}
          subtext="Processed ledger transactions"
          variant="info"
          icon={
            <Scale className="w-5 h-5 text-indigo-400" />
          }
        />

        <KPICard
          title="Match Health Rate"
          value={formatPercent(summary?.reconciliation_rate ?? health?.match_rate, 1)}
          subtext={`Health status: ${health?.status || 'Active'}`}
          variant={(summary?.reconciliation_rate ?? 100) >= 90 ? 'success' : 'warning'}
          onClick={() => navigate('/reconciliation')}
          icon={
            <CheckCircle className="w-5 h-5 text-emerald-400" />
          }
        />

        <KPICard
          title="Open Exceptions"
          value={workflowSummary?.open ?? summary?.open_exceptions_count ?? exceptionsData?.open_exceptions ?? 0}
          subtext="Requiring human review"
          variant={(summary?.open_exceptions_count ?? 0) > 0 ? 'danger' : 'default'}
          onClick={() => navigate('/exceptions')}
          icon={
            <AlertCircle className="w-5 h-5 text-rose-400" />
          }
        />

        <KPICard
          title="AI Agent Investigations"
          value={summary?.active_investigations_count ?? investigationsData?.total_investigations ?? 0}
          subtext={`${investigationsData?.resolved_count || 0} resolved autonomously`}
          variant="default"
          onClick={() => navigate('/agent')}
          icon={
            <Bot className="w-5 h-5 text-indigo-400" />
          }
        />
      </div>

      {/* Exception Management Workflow Strip */}
      {workflowSummary && (
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-md">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-indigo-400" />
              <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                Human-in-the-Loop Workflow Strip
              </h3>
            </div>
            <button
              type="button"
              onClick={() => navigate('/exceptions')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 transition-colors"
            >
              <span>Manage Exceptions</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
            <div
              onClick={() => navigate('/exceptions')}
              className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 cursor-pointer transition-all"
            >
              <div className="text-[10px] text-slate-400">Total Exceptions</div>
              <div className="text-base font-bold text-slate-100 font-mono mt-0.5">
                {workflowSummary.total}
              </div>
            </div>

            <div
              onClick={() => navigate('/exceptions')}
              className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 hover:border-red-500/40 cursor-pointer transition-all"
            >
              <div className="text-[10px] text-red-300 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                <span>Open</span>
              </div>
              <div className="text-base font-bold text-red-400 font-mono mt-0.5">
                {workflowSummary.open}
              </div>
            </div>

            <div
              onClick={() => navigate('/exceptions')}
              className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 hover:border-cyan-500/40 cursor-pointer transition-all"
            >
              <div className="text-[10px] text-cyan-300 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <span>Investigating</span>
              </div>
              <div className="text-base font-bold text-cyan-400 font-mono mt-0.5">
                {workflowSummary.investigating}
              </div>
            </div>

            <div
              onClick={() => navigate('/exceptions')}
              className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 hover:border-indigo-500/40 cursor-pointer transition-all"
            >
              <div className="text-[10px] text-indigo-300 flex items-center gap-1">
                <Users className="w-3 h-3" />
                <span>Unassigned</span>
              </div>
              <div className="text-base font-bold text-indigo-400 font-mono mt-0.5">
                {workflowSummary.unassigned}
              </div>
            </div>

            <div
              onClick={() => navigate('/exceptions')}
              className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 hover:border-emerald-500/40 cursor-pointer transition-all"
            >
              <div className="text-[10px] text-emerald-300 flex items-center gap-1">
                <CheckCircle className="w-3 h-3" />
                <span>Resolved Today</span>
              </div>
              <div className="text-base font-bold text-emerald-400 font-mono mt-0.5">
                {workflowSummary.resolved_today}
              </div>
            </div>

            <div
              onClick={() => navigate('/exceptions')}
              className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 hover:border-rose-500/40 cursor-pointer transition-all"
            >
              <div className="text-[10px] text-rose-300 flex items-center gap-1">
                <ShieldAlert className="w-3 h-3" />
                <span>Escalated</span>
              </div>
              <div className="text-base font-bold text-rose-400 font-mono mt-0.5">
                {workflowSummary.escalated}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Grid: Health Donut + Exception Distribution + Agent Triage */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ReconciliationHealth health={health} onActionClick={() => navigate('/reconciliation')} />
        <ExceptionOverview exceptionData={exceptionsData} />
        <AgentOverview investigationData={investigationsData} />
      </div>

      {/* Recent Activity Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentExceptions exceptions={exceptionsData?.recent_exceptions || []} />
        <RecentInvestigations investigations={investigationsData?.recent_investigations || []} />
      </div>
    </div>
  )
}
