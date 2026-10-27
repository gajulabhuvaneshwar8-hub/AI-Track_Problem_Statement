import React from 'react'
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  ShieldAlert,
} from '../common/Icons'
import SeverityBadge from './SeverityBadge'
import ExceptionStatusBadge from './ExceptionStatusBadge'
import AssignmentControl from './AssignmentControl'

export default function ExceptionTable({
  exceptions = [],
  total = 0,
  page = 1,
  pageSize = 20,
  onPageChange,
  onSelectException,
  onAssignException,
  assignees = [],
  isLoading = false,
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  if (!isLoading && exceptions.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-12 text-center backdrop-blur-md">
        <div className="w-12 h-12 rounded-full bg-slate-800/60 flex items-center justify-center mx-auto mb-3 text-slate-500">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-slate-200 mb-1">
          No Reconciliation Exceptions Found
        </h3>
        <p className="text-xs text-slate-400 max-w-sm mx-auto">
          No exceptions match the current filter criteria, or all discrepancies have been resolved.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden backdrop-blur-md shadow-xl flex flex-col">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800/80 bg-slate-950/40 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              <th className="py-3.5 px-4">Ticket</th>
              <th className="py-3.5 px-4">Title & Discrepancy</th>
              <th className="py-3.5 px-4">Severity</th>
              <th className="py-3.5 px-4">Status</th>
              <th className="py-3.5 px-4">Variance Amount</th>
              <th className="py-3.5 px-4">Assignee</th>
              <th className="py-3.5 px-4">Created</th>
              <th className="py-3.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 text-xs">
            {exceptions.map((exc) => {
              const isEscalated = Boolean(exc.escalated_at)
              return (
                <tr
                  key={exc.id}
                  className="hover:bg-slate-800/30 transition-colors group cursor-pointer"
                  onClick={() => onSelectException(exc.id)}
                >
                  {/* Ticket ID & Category */}
                  <td className="py-3.5 px-4 font-mono text-[11px] text-slate-400">
                    <div className="flex items-center gap-1.5 font-semibold text-indigo-400">
                      <span>EXP-{exc.id.slice(0, 6).toUpperCase()}</span>
                      {isEscalated && (
                        <ShieldAlert
                          className="w-3.5 h-3.5 text-rose-400 shrink-0"
                          title="Ticket Escalated"
                        />
                      )}
                    </div>
                    {exc.category && (
                      <div className="text-[10px] text-slate-500 truncate max-w-[100px]">
                        {exc.category.replace(/_/g, ' ')}
                      </div>
                    )}
                  </td>

                  {/* Title & Description */}
                  <td className="py-3.5 px-4 max-w-xs">
                    <div className="font-semibold text-slate-200 group-hover:text-indigo-300 transition-colors truncate">
                      {exc.title}
                    </div>
                    {exc.description && (
                      <div className="text-[11px] text-slate-400 truncate">
                        {exc.description}
                      </div>
                    )}
                  </td>

                  {/* Severity */}
                  <td className="py-3.5 px-4">
                    <SeverityBadge severity={exc.severity} size="xs" />
                  </td>

                  {/* Status */}
                  <td className="py-3.5 px-4">
                    <ExceptionStatusBadge status={exc.status} size="xs" />
                  </td>

                  {/* Amount */}
                  <td className="py-3.5 px-4 font-mono font-semibold text-slate-200">
                    {exc.amount !== null && exc.amount !== undefined ? (
                      <span>
                        <span className="text-[10px] text-slate-500 font-normal mr-1">
                          {exc.currency || 'INR'}
                        </span>
                        {Number(exc.amount).toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                        })}
                      </span>
                    ) : (
                      <span className="text-slate-500 font-normal text-xs">—</span>
                    )}
                  </td>

                  {/* Assignee Control */}
                  <td
                    className="py-3.5 px-4"
                    onClick={(e) => e.stopPropagation()} // Prevent row click when assigning
                  >
                    <AssignmentControl
                      currentAssigneeId={exc.assigned_to}
                      currentAssigneeName={exc.assignee_name}
                      assignees={assignees}
                      onAssign={(userId) => onAssignException(exc.id, userId)}
                      size="sm"
                    />
                  </td>

                  {/* Created */}
                  <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px] whitespace-nowrap">
                    {new Date(exc.created_at).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </td>

                  {/* Actions */}
                  <td className="py-3.5 px-4 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        onSelectException(exc.id)
                      }}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors border border-slate-700"
                    >
                      <span>Review</span>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing{' '}
            <strong className="text-slate-200">
              {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)}
            </strong>{' '}
            of <strong className="text-slate-200">{total}</strong> exceptions
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-mono font-medium text-slate-300">
              {page} / {totalPages}
            </span>
            <button
              type="button"
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
