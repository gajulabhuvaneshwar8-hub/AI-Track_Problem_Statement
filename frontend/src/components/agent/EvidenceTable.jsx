import React from 'react'
import { formatPercent } from '../../utils/formatters'

export default function EvidenceTable({ evidence = [] }) {
  if (!evidence || evidence.length === 0) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 text-center text-xs text-slate-500">
        No evidence items logged for this investigation
      </div>
    )
  }

  return (
    <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">Collected Evidence & Verification Signals</h3>
          <p className="text-xs text-slate-400 mt-0.5">Automated signal collection from payment gateways and bank journals</p>
        </div>
        <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-full border border-indigo-500/20">
          {evidence.length} Evidence Artifacts
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
              <th className="py-2.5 px-3">Type</th>
              <th className="py-2.5 px-3">Source</th>
              <th className="py-2.5 px-3">Description</th>
              <th className="py-2.5 px-3">Confidence Impact</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {evidence.map((item, idx) => {
              const impact = item.confidence_impact ?? item.impact ?? null
              return (
                <tr key={item.id || idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 uppercase tracking-wide">
                      {item.evidence_type || item.type || 'Data Signal'}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-medium text-slate-300 capitalize">
                    {item.source || 'Reconciliation Engine'}
                  </td>
                  <td className="py-3 px-3 text-slate-300 leading-relaxed max-w-md">
                    {item.description || item.finding || JSON.stringify(item.details || item)}
                  </td>
                  <td className="py-3 px-3 font-semibold">
                    {impact !== null ? (
                      <span className={impact >= 0.7 ? 'text-emerald-400' : 'text-amber-400'}>
                        {formatPercent(impact * 100, 0)}
                      </span>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
