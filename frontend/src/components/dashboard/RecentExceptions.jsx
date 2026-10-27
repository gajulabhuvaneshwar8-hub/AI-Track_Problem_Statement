import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import StatusBadge from '../common/StatusBadge'
import { formatCurrency, formatDateTime } from '../../utils/formatters'

export default function RecentExceptions({ exceptions = [] }) {
  const navigate = useNavigate()

  return (
    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">Recent Exceptions</h3>
          <p className="text-xs text-slate-400 mt-0.5">High-priority mismatches requiring attention</p>
        </div>
        <Link
          to="/exceptions"
          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          View All &rarr;
        </Link>
      </div>

      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
              <th className="py-2.5 px-3">Category</th>
              <th className="py-2.5 px-3">Severity</th>
              <th className="py-2.5 px-3">Amount</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {exceptions.map((exc) => (
              <tr key={exc.id} className="hover:bg-slate-800/30 transition-colors">
                <td className="py-3 px-3">
                  <p className="font-semibold text-slate-200 capitalize">{exc.category.replace(/_/g, ' ')}</p>
                  <p className="text-[10px] text-slate-400">{formatDateTime(exc.created_at)}</p>
                </td>
                <td className="py-3 px-3">
                  <StatusBadge status={exc.severity} size="xs" />
                </td>
                <td className="py-3 px-3 font-semibold text-slate-100">
                  {formatCurrency(exc.amount, exc.currency)}
                </td>
                <td className="py-3 px-3">
                  <StatusBadge status={exc.status} size="xs" />
                </td>
                <td className="py-3 px-3 text-right">
                  <button
                    onClick={() => navigate(`/agent?exceptionId=${exc.id}`)}
                    className="px-2.5 py-1 text-[11px] font-medium rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 transition-colors"
                  >
                    Investigate
                  </button>
                </td>
              </tr>
            ))}
            {exceptions.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-xs text-slate-500">
                  No recent exceptions recorded
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
