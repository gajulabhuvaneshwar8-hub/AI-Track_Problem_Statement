import React from 'react'

export default function KPICard({
  title,
  value,
  subtext = null,
  icon = null,
  trend = null, // e.g. { label: '+12%', positive: true }
  variant = 'default', // 'default' | 'success' | 'warning' | 'danger' | 'info'
  onClick = null,
}) {
  const variantStyles = {
    default: 'from-slate-900/90 to-slate-900/40 border-slate-800 hover:border-slate-700',
    success: 'from-emerald-950/30 to-slate-900/40 border-emerald-500/20 hover:border-emerald-500/40',
    warning: 'from-amber-950/30 to-slate-900/40 border-amber-500/20 hover:border-amber-500/40',
    danger: 'from-red-950/30 to-slate-900/40 border-red-500/20 hover:border-red-500/40',
    info: 'from-indigo-950/30 to-slate-900/40 border-indigo-500/20 hover:border-indigo-500/40',
  }

  return (
    <div
      onClick={onClick}
      className={`relative p-5 rounded-2xl bg-gradient-to-b ${variantStyles[variant] || variantStyles.default} border shadow-sm transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:shadow-md hover:scale-[1.01]' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</p>
          <h3 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mt-1.5">{value}</h3>
        </div>
        {icon && (
          <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/50 text-indigo-400">
            {icon}
          </div>
        )}
      </div>

      {(subtext || trend) && (
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-800/60 text-xs">
          {trend && (
            <span
              className={`font-semibold inline-flex items-center gap-0.5 ${
                trend.positive ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {trend.label}
            </span>
          )}
          {subtext && <span className="text-slate-400">{subtext}</span>}
        </div>
      )}
    </div>
  )
}
