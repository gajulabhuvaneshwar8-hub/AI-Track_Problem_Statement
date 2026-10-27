/**
 * healthService.js — calls the backend /api/health endpoint.
 */

import api from './api'

/**
 * @returns {Promise<{status: string, service: string, timestamp: string}>}
 */
export async function checkHealth() {
  const response = await api.get('/health')
  return response.data
}
