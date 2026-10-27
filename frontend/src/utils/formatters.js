/**
 * formatters.js
 * Utility formatting functions for financial values, dates, percentages, and badges.
 */

export function formatCurrency(value, currency = 'INR') {
  if (value === null || value === undefined || value === '') return '—'
  const num = typeof value === 'string' ? parseFloat(value) : Number(value)
  if (Number.isNaN(num)) return '—'

  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency || 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num)
  } catch {
    // Fallback if currency code is unusual
    return `${currency} ${num.toFixed(2)}`
  }
}

export function formatPercent(value, decimals = 1) {
  if (value === null || value === undefined || value === '') return '—'
  const num = typeof value === 'string' ? parseFloat(value) : Number(value)
  if (Number.isNaN(num)) return '—'
  return `${num.toFixed(decimals)}%`
}

export function formatDateTime(isoString) {
  if (!isoString) return '—'
  try {
    const d = new Date(isoString)
    if (Number.isNaN(d.getTime())) return '—'
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    })
  } catch {
    return String(isoString)
  }
}

export function formatDate(isoString) {
  if (!isoString) return '—'
  try {
    const d = new Date(isoString)
    if (Number.isNaN(d.getTime())) return '—'
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return String(isoString)
  }
}

export function truncateId(id, start = 8, end = 4) {
  if (!id) return '—'
  const str = String(id)
  if (str.length <= start + end) return str
  return `${str.substring(0, start)}...${str.substring(str.length - end)}`
}
