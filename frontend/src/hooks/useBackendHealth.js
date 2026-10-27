/**
 * useBackendHealth.js — custom hook that polls backend /health.
 */

import { useCallback, useEffect, useState } from 'react'
import { checkHealth } from '../services/healthService'

/**
 * @param {number} [pollInterval=30000] — ms between polls (0 = no polling)
 */
export function useBackendHealth(pollInterval = 30_000) {
  const [status, setStatus]       = useState('loading')  // 'loading' | 'ok' | 'error'
  const [data,   setData]         = useState(null)
  const [error,  setError]        = useState(null)
  const [lastChecked, setLastChecked] = useState(null)

  const check = useCallback(async () => {
    setStatus('loading')
    setError(null)
    try {
      const result = await checkHealth()
      setData(result)
      setStatus('ok')
    } catch (err) {
      setError(err?.message ?? 'Backend unreachable')
      setStatus('error')
    } finally {
      setLastChecked(new Date())
    }
  }, [])

  useEffect(() => {
    check()
    if (pollInterval > 0) {
      const id = setInterval(check, pollInterval)
      return () => clearInterval(id)
    }
  }, [check, pollInterval])

  return { status, data, error, lastChecked, refresh: check }
}
