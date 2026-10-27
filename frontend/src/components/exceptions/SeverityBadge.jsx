import { AlertCircle, AlertTriangle, Info, ShieldAlert } from '../common/Icons'

const SEVERITY_CONFIG = {
  critical: {
    label: 'Critical',
    bg: 'bg-red-500/10 border-red-500/30 text-red-400',
    dot: 'bg-red-500',
    icon: ShieldAlert,
  },
  high: {
    label: 'High',
    bg: 'bg-orange-500/10 border-orange-500/30 text-orange-400',
    dot: 'bg-orange-400',
    icon: AlertCircle,
  },
  medium: {
    label: 'Medium',
    bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
    dot: 'bg-amber-400',
    icon: AlertTriangle,
  },
  low: {
    label: 'Low',
    bg: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
    dot: 'bg-blue-400',
    icon: Info,
  },
}

export default function SeverityBadge({ severity, size = 'sm', showIcon = true }) {
  const key = String(severity || 'medium').toLowerCase()
  const config = SEVERITY_CONFIG[key] || SEVERITY_CONFIG.medium
  const Icon = config.icon

  const sizeClass = size === 'xs' 
    ? 'text-xs px-2 py-0.5' 
    : size === 'lg'
    ? 'text-sm px-3 py-1 font-semibold'
    : 'text-xs px-2.5 py-1'

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium transition-colors ${config.bg} ${sizeClass}`}
      title={`Severity: ${config.label}`}
    >
      {showIcon && <Icon className="w-3.5 h-3.5 shrink-0" />}
      <span>{config.label}</span>
    </span>
  )
}
