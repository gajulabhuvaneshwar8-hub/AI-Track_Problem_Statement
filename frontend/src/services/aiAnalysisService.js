/**
 * aiAnalysisService.js
 * API client methods for AI mismatch analysis, root cause explanations,
 * risk reasoning, and investigation checklists.
 */

import api from './api'

/**
 * Trigger or fetch AI analysis for a reconciliation result
 */
export async function analyzeReconciliation(reconciliationId, force = false, analysisType = 'exception_analysis') {
  const response = await api.post(`/ai/analyze/${reconciliationId}`, null, {
    params: { force, analysis_type: analysisType },
  })
  return response.data
}

/**
 * Trigger or fetch AI analysis for an exception ticket
 */
export async function analyzeException(exceptionId, force = false, analysisType = 'exception_analysis') {
  const response = await api.post(`/ai/analyze/exception/${exceptionId}`, null, {
    params: { force, analysis_type: analysisType },
  })
  return response.data
}

/**
 * Perform a deep diagnostic investigation of an exception
 */
export async function investigateException(exceptionId, force = false) {
  const response = await api.post(`/ai/investigate/${exceptionId}`, null, {
    params: { force },
  })
  return response.data
}

/**
 * Fetch paginated list of historical AI analyses
 */
export async function listAnalyses(params = {}) {
  const response = await api.get('/ai/analyses', { params })
  return response.data
}

/**
 * Fetch a single AI analysis by ID
 */
export async function getAnalysis(analysisId) {
  const response = await api.get(`/ai/analyses/${analysisId}`)
  return response.data
}

/**
 * Fetch all analyses recorded for a specific reconciliation result
 */
export async function getAnalysesForReconciliation(reconciliationId) {
  const response = await api.get(`/ai/analyses/reconciliation/${reconciliationId}`)
  return response.data
}
