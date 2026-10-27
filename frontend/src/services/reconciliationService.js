/**
 * reconciliationService.js
 * API service for triggering reconciliation runs and fetching results/summaries.
 */

import api from './api'

/**
 * Trigger reconciliation run for a given merchant (or platform-wide)
 */
export async function runReconciliation(merchantId = null) {
  const payload = merchantId ? { merchant_id: merchantId } : {}
  const response = await api.post('/reconciliation/run', payload)
  return response.data
}

/**
 * Fetch paginated reconciliation results with optional filters
 */
export async function getReconciliationResults(params = {}) {
  const response = await api.get('/reconciliation/results', { params })
  return response.data
}

/**
 * Fetch single reconciliation result detail by ID
 */
export async function getReconciliationResult(resultId) {
  const response = await api.get(`/reconciliation/results/${resultId}`)
  return response.data
}

/**
 * Fetch reconciliation summary for a merchant
 */
export async function getReconciliationSummary(merchantId) {
  const response = await api.get(`/reconciliation/summary/${merchantId}`)
  return response.data
}

/**
 * Fetch merchants to populate selector dropdown
 */
export async function getMerchants(params = { page: 1, page_size: 100 }) {
  const response = await api.get('/merchants', { params })
  return response.data
}

export const reconciliationService = {
  runReconciliation,
  getReconciliationResults,
  getReconciliationResult,
  getReconciliationSummary,
  getMerchants,
}

export default reconciliationService

