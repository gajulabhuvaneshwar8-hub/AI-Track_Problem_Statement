/**
 * transactionService.js
 * API service for querying and managing transactions.
 */

import api from './api'

export const transactionService = {
  async listTransactions(params = {}) {
    const response = await api.get('/transactions', { params })
    return response.data
  },

  async getTransaction(transactionId) {
    const response = await api.get(`/transactions/${transactionId}`)
    return response.data
  },

  async createTransaction(payload) {
    const response = await api.post('/transactions', payload)
    return response.data
  },

  async updateTransaction(transactionId, payload) {
    const response = await api.put(`/transactions/${transactionId}`, payload)
    return response.data
  },
}

export default transactionService
