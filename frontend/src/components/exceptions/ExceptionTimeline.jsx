import React from 'react'
import {
  AlertCircle,
  Bot,
  CheckCircle,
  Clock,
  EyeOff,
  FileText,
  HelpCircle,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  User,
  UserCheck,
} from '../common/Icons'

const EVENT_TYPE_MAP = {
  exception_created: {
    label: 'Ticket Created',
    icon: AlertCircle,
    color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  },
  exception_assigned: {
    label: 'Assignment Changed',
    icon: UserCheck,
    color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
  },
  exception_status_changed: {
    label: 'Status Transition',
    icon: Clock,
    color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  },
  exception_reviewed: {
    label: 'Review Note',
    icon: FileText,
    color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  },
  exception_resolved: {
    label: 'Resolved',
    icon: CheckCircle,
    color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  },
  exception_ignored: {
    label: 'Ignored',
    icon: EyeOff,
    color: 'text-slate-400 bg-slate-500/10 border-slate-500/20',
  },
  exception_escalated: {
    label: 'Escalated',
    icon: ShieldAlert,
    color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
  },
  exception_reopened: {
    label: 'Reopened',
    icon: RotateCcw,
    color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  },
  ai_analysis: {
    label: 'AI Mismatch Analysis',
    icon: Sparkles,
    color: 'text-violet-400 bg-violet-500/10 border-violet-500/20',
  },
  agent_investigation: {
    label: 'Autonomous Agent Investigation',
    icon: Bot,
    color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  },
}

export default function ExceptionTimeline({ events = [] }) {
  if (!events || events.length === 0) {
    return (
      <div className="py-8 text-center text-xs text-slate-500 italic bg-slate-950/40 rounded-xl border border-slate-800/60">
        No audit events recorded yet for this exception ticket.
      </div>
    )
  }

  return (
    <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gradient-to-b before:from-indigo-500/40 before:via-slate-700/40 before:to-slate-800/20">
      {events.map((event, idx) => {
        const config = EVENT_TYPE_MAP[event.event_type] || {
          label: event.event_type.replace(/_/g, ' '),
          icon: HelpCircle,
          color: 'text-slate-400 bg-slate-800/80 border-slate-700',
        }
        const Icon = config.icon
        const dateObj = new Date(event.timestamp)
        const formattedDate = dateObj.toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })
        const formattedTime = dateObj.toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })

        return (
          <div key={event.id || idx} className="relative group">
            {/* Timeline node icon */}
            <div
              className={`absolute -left-[29px] top-1 w-6 h-6 rounded-full border flex items-center justify-center shadow-lg transition-transform group-hover:scale-110 ${config.color}`}
            >
              <Icon className="w-3.5 h-3.5" />
            </div>

            {/* Event content box */}
            <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 hover:border-slate-700/80 transition-all shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-200">
                    {event.title || config.label}
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full border font-medium uppercase tracking-wider ${config.color}`}
                  >
                    {config.label}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                  <span>{formattedDate}</span>
                  <span>•</span>
                  <span>{formattedTime}</span>
                </div>
              </div>

              {event.description && (
                <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                  {event.description}
                </p>
              )}

              {/* Actor pill */}
              <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
                <div className="flex items-center gap-1.5">
                  <User className="w-3 h-3 text-slate-500" />
                  <span className="font-medium text-slate-300">
                    {event.actor || 'System'}
                  </span>
                  {event.actor_role && (
                    <span className="text-slate-500">({event.actor_role})</span>
                  )}
                </div>

                {event.metadata && Object.keys(event.metadata).length > 0 && (
                  <details className="text-[10px] text-slate-500 cursor-pointer">
                    <summary className="hover:text-slate-400 transition-colors select-none">
                      Details
                    </summary>
                    <pre className="mt-1 p-1.5 bg-slate-950 rounded border border-slate-800 text-[10px] text-slate-400 overflow-x-auto max-w-xs">
                      {JSON.stringify(event.metadata, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
