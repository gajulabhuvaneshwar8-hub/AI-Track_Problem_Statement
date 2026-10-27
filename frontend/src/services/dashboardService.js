/**
 * dashboardService.js
 * API service for the Finance Operations Control Center dashboard.
 */

import api from './api'

export const dashboardService = {
  async getSummary(merchantId = null) {
    const params = merchantId ? { merchant_id: merchantId } : {}
    const response = await api.get('/dashboard/summary', { params })
    return response.data
  },

  async getExceptions(merchantId = null) {
    const params = merchantId ? { merchant_id: merchantId } : {}
    const response = await api.get('/dashboard/exceptions', { params })
    return response.data
  },

  async getInvestigations(merchantId = null) {
    const params = merchantId ? { merchant_id: merchantId } : {}
    const response = await api.get('/dashboard/investigations', { params })
    return response.data
  },

  async getReconciliationHealth(merchantId = null) {
    const params = merchantId ? { merchant_id: merchantId } : {}
    const response = await api.get('/dashboard/reconciliation-health', { params })
    return response.data
  },
}

export default dashboardService
