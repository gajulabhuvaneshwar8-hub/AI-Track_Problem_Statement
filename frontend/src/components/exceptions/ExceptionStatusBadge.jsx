import { AlertCircle, CheckCircle, Clock, EyeOff, ShieldAlert } from '../common/Icons'

const STATUS_CONFIG = {
  open: {
    label: 'Open',
    bg: 'bg-red-500/10 border-red-500/20 text-red-400',
    dot: 'bg-red-400',
    icon: AlertCircle,
  },
  investigating: {
    label: 'Investigating',
    bg: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400',
    dot: 'bg-cyan-400',
    icon: Clock,
  },
  resolved: {
    label: 'Resolved',
    bg: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
    dot: 'bg-emerald-400',
    icon: CheckCircle,
  },
  ignored: {
    label: 'Ignored',
    bg: 'bg-slate-500/10 border-slate-500/20 text-slate-400',
    dot: 'bg-slate-400',
    icon: EyeOff,
  },
  escalated: {
    label: 'Escalated',
    bg: 'bg-rose-500/10 border-rose-500/20 text-rose-400',
    dot: 'bg-rose-400',
    icon: ShieldAlert,
  },
}

export default function ExceptionStatusBadge({ status, size = 'sm', showDot = true }) {
  const key = String(status || 'open').toLowerCase()
  const config = STATUS_CONFIG[key] || STATUS_CONFIG.open
  const Icon = config.icon

  const sizeClass = size === 'xs'
    ? 'text-xs px-2 py-0.5'
    : size === 'lg'
    ? 'text-sm px-3 py-1 font-semibold'
    : 'text-xs px-2.5 py-1'

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium transition-colors ${config.bg} ${sizeClass}`}
      title={`Status: ${config.label}`}
    >
      {showDot && (
        <span className={`w-1.5 h-1.5 rounded-full ${config.dot} animate-pulse`} />
      )}
      <Icon className="w-3.5 h-3.5 shrink-0" />
      <span>{config.label}</span>
    </span>
  )
}
