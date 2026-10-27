import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import StatusBadge from '../common/StatusBadge'
import { formatDateTime, formatPercent } from '../../utils/formatters'

export default function RecentInvestigations({ investigations = [] }) {
  const navigate = useNavigate()

  return (
    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">Recent AI Agent Decisions</h3>
          <p className="text-xs text-slate-400 mt-0.5">Automated triage decisions and audit trails</p>
        </div>
        <Link
          to="/agent"
          className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          View All &rarr;
        </Link>
      </div>

      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
              <th className="py-2.5 px-3">Decision</th>
              <th className="py-2.5 px-3">Recommended Action</th>
              <th className="py-2.5 px-3">Confidence</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {investigations.map((inv) => (
              <tr key={inv.id} className="hover:bg-slate-800/30 transition-colors">
                <td className="py-3 px-3">
                  <p className="font-semibold text-slate-200 capitalize">
                    {inv.decision ? inv.decision.replace(/_/g, ' ') : 'Pending'}
                  </p>
                  <p className="text-[10px] text-slate-400">{formatDateTime(inv.created_at)}</p>
                </td>
                <td className="py-3 px-3">
                  <StatusBadge status={inv.recommended_action} size="xs" />
                </td>
                <td className="py-3 px-3 font-semibold text-slate-200">
                  {inv.confidence_score !== null ? formatPercent(inv.confidence_score * 100, 0) : '—'}
                </td>
                <td className="py-3 px-3">
                  <StatusBadge status={inv.status} size="xs" />
                </td>
                <td className="py-3 px-3 text-right">
                  <button
                    onClick={() => navigate(`/agent?investigationId=${inv.id}`)}
                    className="px-2.5 py-1 text-[11px] font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
            {investigations.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-xs text-slate-500">
                  No recent investigations recorded
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
