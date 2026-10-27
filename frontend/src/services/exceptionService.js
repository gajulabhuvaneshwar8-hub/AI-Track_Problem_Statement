/**
 * exceptionService.js
 * Comprehensive API service for Step 9: Exception Management & Human-in-the-Loop workflow.
 * Manages full lifecycle: listing, filtering, deep details, grounded timelines,
 * assignments, review notes, resolution, ignoring, escalation, reopening, and workflow summary.
 */

import api from './api'

export const exceptionService = {
  /**
   * List exceptions with server-side pagination, filters, and keyword search.
   */
  async listExceptions(params = {}) {
    const response = await api.get('/exceptions', { params })
    return response.data
  },

  /**
   * Get basic exception metadata.
   */
  async getException(exceptionId) {
    const response = await api.get(`/exceptions/${exceptionId}`)
    return response.data
  },

  /**
   * Get full 360-degree context: exception, transaction, bank transaction,
   * reconciliation result, latest AI analysis, agent investigation, and assignee.
   */
  async getExceptionDetails(exceptionId) {
    const response = await api.get(`/exceptions/${exceptionId}/details`)
    return response.data
  },

  /**
   * Get chronological audit and event timeline.
   */
  async getExceptionTimeline(exceptionId) {
    const response = await api.get(`/exceptions/${exceptionId}/timeline`)
    return response.data
  },

  /**
   * Assign or unassign an exception to an analyst.
   */
  async assignException(exceptionId, assignedTo) {
    const response = await api.post(`/exceptions/${exceptionId}/assign`, {
      assigned_to: assignedTo,
    })
    return response.data
  },

  /**
   * Transition exception workflow status (e.g. open -> investigating).
   */
  async updateStatus(exceptionId, status, note = null) {
    const response = await api.post(`/exceptions/${exceptionId}/status`, {
      status,
      note,
    })
    return response.data
  },

  /**
   * Add human investigation / review note. Auto-transitions open -> investigating.
   */
  async addReviewNote(exceptionId, note) {
    const response = await api.post(`/exceptions/${exceptionId}/review`, {
      note,
    })
    return response.data
  },

  /**
   * Mark exception as resolved with mandatory rationale.
   */
  async resolveException(exceptionId, resolutionNote) {
    const response = await api.post(`/exceptions/${exceptionId}/resolve`, {
      resolution_note: resolutionNote,
    })
    return response.data
  },

  /**
   * Mark exception as ignored with mandatory reason.
   */
  async ignoreException(exceptionId, reason) {
    const response = await api.post(`/exceptions/${exceptionId}/ignore`, {
      reason,
    })
    return response.data
  },

  /**
   * Escalate exception internally with reason and optional target team.
   */
  async escalateException(exceptionId, reason, suggestedTeam = null) {
    const response = await api.post(`/exceptions/${exceptionId}/escalate`, {
      reason,
      suggested_team: suggestedTeam,
    })
    return response.data
  },

  /**
   * Reopen a resolved or ignored exception with audit explanation.
   */
  async reopenException(exceptionId, reason = null) {
    const response = await api.post(`/exceptions/${exceptionId}/reopen`, {
      reason,
    })
    return response.data
  },

  /**
   * Get list of active team members assignable to exceptions.
   */
  async listAssignees() {
    const response = await api.get('/exceptions/assignees')
    return response.data
  },

  /**
   * Get aggregated workflow counts across all workflow states.
   */
  async getWorkflowSummary(merchantId = null) {
    const params = merchantId ? { merchant_id: merchantId } : {}
    const response = await api.get('/exceptions/workflow-summary', { params })
    return response.data
  },

  /**
   * Direct model update.
   */
  async updateException(exceptionId, payload) {
    const response = await api.put(`/exceptions/${exceptionId}`, payload)
    return response.data
  },

  /**
   * Manual exception ticket creation.
   */
  async createException(payload) {
    const response = await api.post('/exceptions', payload)
    return response.data
  },
}

export default exceptionService
