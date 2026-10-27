/**
 * HealthBadge.jsx — displays backend connection status.
 */

import { useBackendHealth } from '../hooks/useBackendHealth'

const STATUS_LABEL = { loading: 'Connecting…', ok: 'Backend Connected', error: 'Backend Offline' }
const STATUS_COLOR = {
  loading: 'text-amber-400 border-amber-400/30 bg-amber-400/10',
  ok:      'text-emerald-400 border-emerald-400/30 bg-emerald-400/10',
  error:   'text-red-400    border-red-400/30    bg-red-400/10',
}

export default function HealthBadge() {
  const { status, data, error, lastChecked, refresh } = useBackendHealth(30_000)

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium
                  transition-all duration-300 ${STATUS_COLOR[status]}`}
    >
      {/* Animated dot */}
      <span className="relative flex h-2 w-2">
        {status === 'ok' && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        )}
        <span
          className={`relative inline-flex rounded-full h-2 w-2 status-dot ${status}`}
        />
      </span>

      {STATUS_LABEL[status]}

      {status === 'ok' && data?.service && (
        <span className="text-emerald-400/60">· {data.service}</span>
      )}

      {status === 'error' && (
        <>
          {error && <span className="text-red-400/60">· {error}</span>}
          <button
            onClick={refresh}
            className="ml-1 underline text-red-300 hover:text-red-100 transition-colors"
            title="Retry"
          >
            Retry
          </button>
        </>
      )}

      {lastChecked && (
        <span className="text-current/40 ml-1">
          {lastChecked.toLocaleTimeString()}
        </span>
      )}
    </div>
  )
}
