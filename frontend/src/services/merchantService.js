/**
 * merchantService.js
 * API service for merchant configuration and listings.
 */

import api from './api'

export const merchantService = {
  async listMerchants(params = { page: 1, page_size: 100 }) {
    const response = await api.get('/merchants', { params })
    return response.data
  },

  async getMerchant(merchantId) {
    const response = await api.get(`/merchants/${merchantId}`)
    return response.data
  },

  async createMerchant(payload) {
    const response = await api.post('/merchants', payload)
    return response.data
  },

  async updateMerchant(merchantId, payload) {
    const response = await api.put(`/merchants/${merchantId}`, payload)
    return response.data
  },
}

export default merchantService
