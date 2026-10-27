import React from 'react'
import LoadingSpinner from './LoadingSpinner'
import EmptyState from './EmptyState'

export default function DataTable({
  columns = [],
  data = [],
  loading = false,
  emptyTitle = 'No data available',
  emptyMessage = 'There are no records matching your query.',
  pagination = null,
  onRowClick = null,
  keyField = 'id',
}) {
  const totalPages = pagination ? Math.max(1, Math.ceil(pagination.total / pagination.pageSize)) : 1

  return (
    <div className="w-full bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm flex flex-col">
      <div className="overflow-x-auto w-full">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 font-semibold tracking-wider uppercase text-[11px]">
              {columns.map((col, idx) => (
                <th
                  key={col.header || idx}
                  className={`py-3.5 px-4 ${col.className || ''}`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="py-12 text-center">
                  <LoadingSpinner message="Fetching records..." />
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="py-8">
                  <EmptyState title={emptyTitle} description={emptyMessage} />
                </td>
              </tr>
            ) : (
              data.map((row, rowIdx) => {
                const rowKey = row[keyField] || rowIdx
                const isClickable = Boolean(onRowClick)
                return (
                  <tr
                    key={rowKey}
                    onClick={() => isClickable && onRowClick(row)}
                    className={`transition-colors ${
                      isClickable ? 'cursor-pointer hover:bg-slate-800/50' : 'hover:bg-slate-800/30'
                    }`}
                  >
                    {columns.map((col, colIdx) => (
                      <td
                        key={colIdx}
                        className={`py-3.5 px-4 text-xs font-normal align-middle ${col.className || ''}`}
                      >
                        {col.render
                          ? col.render(row[col.accessor], row, rowIdx)
                          : col.accessor
                          ? row[col.accessor] ?? '—'
                          : null}
                      </td>
                    ))}
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      {pagination && !loading && data.length > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between px-4 py-3 border-t border-slate-800 bg-slate-900/40 text-xs text-slate-400 gap-2">
          <div>
            Showing{' '}
            <span className="font-semibold text-slate-200">
              {Math.min((pagination.page - 1) * pagination.pageSize + 1, pagination.total)}
            </span>{' '}
            to{' '}
            <span className="font-semibold text-slate-200">
              {Math.min(pagination.page * pagination.pageSize, pagination.total)}
            </span>{' '}
            of <span className="font-semibold text-slate-200">{pagination.total}</span> records
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => pagination.onPageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
              className="px-2.5 py-1 rounded border border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <span className="px-2 font-medium text-slate-300">
              {pagination.page} of {totalPages}
            </span>
            <button
              onClick={() => pagination.onPageChange(pagination.page + 1)}
              disabled={pagination.page >= totalPages}
              className="px-2.5 py-1 rounded border border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
