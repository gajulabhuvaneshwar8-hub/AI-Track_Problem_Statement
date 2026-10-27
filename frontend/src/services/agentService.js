/**
 * agentService.js
 * API client methods for Step 7: AI Reconciliation Investigation Agent.
 * Autonomous ledger evidence aggregation, rule-based decisions, and risk evaluation.
 */

import api from './api'

/**
 * Fetch paginated list of AI agent investigations with multi-field filtering.
 */
export async function listInvestigations(params = {}) {
  const response = await api.get('/agents/investigations', { params })
  return response.data
}

/**
 * Fetch a single agent investigation by ID.
 */
export async function getInvestigation(investigationId) {
  const response = await api.get(`/agents/investigations/${investigationId}`)
  return response.data
}

/**
 * Fetch full multi-ledger evidence ledger for a given investigation.
 */
export async function getInvestigationEvidence(investigationId) {
  const response = await api.get(`/agents/investigations/${investigationId}/evidence`)
  return response.data
}

/**
 * Trigger or retrieve an autonomous investigation for a specific Payment Exception.
 */
export async function investigateException(exceptionId, force = false) {
  const response = await api.post(`/agents/investigate/exception/${exceptionId}`, null, {
    params: { force },
  })
  return response.data
}

/**
 * Trigger or retrieve an autonomous investigation for a specific Reconciliation Result.
 */
export async function investigateReconciliation(reconciliationId, force = false) {
  const response = await api.post(`/agents/investigate/reconciliation/${reconciliationId}`, null, {
    params: { force },
  })
  return response.data
}

/**
 * Fetch escalation routing and ticket recommendations for an investigation.
 */
export async function getEscalation(investigationId) {
  const response = await api.get(`/agents/investigations/${investigationId}/escalation`)
  return response.data
}
