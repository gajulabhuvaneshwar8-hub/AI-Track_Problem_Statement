/**
 * settlementService.js
 * API service for querying settlements and batches.
 */

import api from './api'

export const settlementService = {
  async listSettlements(params = {}) {
    const response = await api.get('/settlements', { params })
    return response.data
  },

  async getSettlement(settlementId) {
    const response = await api.get(`/settlements/${settlementId}`)
    return response.data
  },

  async createSettlement(payload) {
    const response = await api.post('/settlements', payload)
    return response.data
  },
}

export default settlementService
