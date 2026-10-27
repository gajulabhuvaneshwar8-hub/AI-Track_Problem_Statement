/**
 * ingestionService.js
 * API service for uploading CSV/Excel data files and fetching import batch history.
 */

import api from './api'

/**
 * Upload a payment gateway transaction file (CSV, XLSX, XLS)
 */
export async function uploadGatewayFile(file, merchantId, onUploadProgress) {
  const formData = new FormData()
  formData.append('file', file)
  if (merchantId) {
    formData.append('merchant_id', merchantId)
  }

  const response = await api.post('/ingestion/gateway', formData, {
    onUploadProgress,
  })
  return response.data
}

/**
 * Upload a bank statement file (CSV, XLSX, XLS)
 */
export async function uploadBankFile(file, merchantId, onUploadProgress) {
  const formData = new FormData()
  formData.append('file', file)
  if (merchantId) {
    formData.append('merchant_id', merchantId)
  }

  const response = await api.post('/ingestion/bank', formData, {
    onUploadProgress,
  })
  return response.data
}

/**
 * Upload a processor settlement file (CSV, XLSX, XLS)
 */
export async function uploadSettlementFile(file, merchantId, onUploadProgress) {
  const formData = new FormData()
  formData.append('file', file)
  if (merchantId) {
    formData.append('merchant_id', merchantId)
  }

  const response = await api.post('/ingestion/settlement', formData, {
    onUploadProgress,
  })
  return response.data
}

/**
 * Fetch paginated import batch history
 */
export async function getImportHistory(params = {}) {
  const response = await api.get('/ingestion/history', { params })
  return response.data
}
