/**
 * DataImport.jsx — Financial data file ingestion interface.
 * Upload CSV/Excel files for Payment Gateway, Bank Statement, and Settlement records.
 */

import React, { useEffect, useRef, useState } from 'react'
import PageHeader from '../components/layout/PageHeader'
import StatusBadge from '../components/common/StatusBadge'
import {
  getImportHistory,
  uploadBankFile,
  uploadGatewayFile,
  uploadSettlementFile,
} from '../services/ingestionService'
import merchantService from '../services/merchantService'
import { formatDateTime } from '../utils/formatters'

const SOURCES = [
  { id: 'gateway', label: 'Gateway', title: 'Payment Gateway', icon: '💳', desc: 'Stripe, Razorpay, PayPal CSV/XLSX exports', endpoint: '/api/ingestion/gateway' },
  { id: 'bank', label: 'Bank', title: 'Bank Statement', icon: '🏦', desc: 'Bank statement feeds and ledger deposits', endpoint: '/api/ingestion/bank' },
  { id: 'settlement', label: 'Settlement', title: 'Settlement Batch', icon: '📑', desc: 'Processor net payout and fee reports', endpoint: '/api/ingestion/settlement' },
]

export default function DataImport() {
  const [selectedSource, setSelectedSource] = useState('gateway')
  const [selectedFile, setSelectedFile] = useState(null)
  const [merchantId, setMerchantId] = useState('')
  const [merchants, setMerchants] = useState([])
  const [loadingMerchants, setLoadingMerchants] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [lastResult, setLastResult] = useState(null)
  const [uploadError, setUploadError] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  const fileInputRef = useRef(null)

  // Fetch import history
  const fetchHistory = async () => {
    setLoadingHistory(true)
    try {
      const data = await getImportHistory({ page: 1, page_size: 15 })
      setHistory(data.items || [])
    } catch (err) {
      console.error('Failed to load import history:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  // Fetch merchants list
  const fetchMerchants = async () => {
    setLoadingMerchants(true)
    try {
      const data = await merchantService.listMerchants({ page: 1, page_size: 100 })
      const list = Array.isArray(data) ? data : (data.items || [])
      setMerchants(list)
    } catch (err) {
      console.error('Failed to load merchants:', err)
    } finally {
      setLoadingMerchants(false)
    }
  }

  useEffect(() => {
    fetchHistory()
    fetchMerchants()
  }, [])

  // Drag and drop event handlers
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0])
    }
  }

  const handleFileSelected = (file) => {
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
      setUploadError("Unsupported file format. Only .csv, .xlsx, and .xls files are supported.")
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File size exceeds maximum 10 MB limit.')
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      return
    }
    setSelectedFile(file)
    setUploadError(null)
    setLastResult(null)
  }

  const handleClearFile = (e) => {
    e?.stopPropagation()
    setSelectedFile(null)
    setUploadError(null)
    setLastResult(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError('Please select a financial export file to upload.')
      return
    }

    setIsUploading(true)
    setUploadProgress(0)
    setUploadError(null)
    setLastResult(null)

    const onProgress = (progressEvent) => {
      if (progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        setUploadProgress(percent)
      }
    }

    try {
      let result
      const targetMerchant = merchantId.trim() || undefined

      if (selectedSource === 'gateway') {
        result = await uploadGatewayFile(selectedFile, targetMerchant, onProgress)
      } else if (selectedSource === 'bank') {
        result = await uploadBankFile(selectedFile, targetMerchant, onProgress)
      } else {
        result = await uploadSettlementFile(selectedFile, targetMerchant, onProgress)
      }

      setLastResult(result)
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      fetchHistory()
    } catch (err) {
      console.error('Upload failed error details:', err)
      // Safe string extraction from backend response
      let errorMsg = 'File ingestion failed. Please verify the file format and try again.'
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail
        if (typeof detail === 'string') {
          errorMsg = detail
        } else if (Array.isArray(detail)) {
          errorMsg = detail.map((d) => d.msg || `${d.loc?.join('.')}: ${d.type}`).join(', ')
        } else if (typeof detail === 'object') {
          errorMsg = JSON.stringify(detail)
        }
      } else if (err.message) {
        errorMsg = err.message
      }
      setUploadError(errorMsg)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Data Ingestion Hub"
        subtitle="Import multi-rail payment transactions, bank feeds, and settlement reports via CSV or Excel"
      />

      {/* Source Selection Header & Radios */}
      <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">Source Type</h3>
            <p className="text-xs text-slate-400">Select target financial ledger for parsing and deduplication</p>
          </div>
          {/* Explicit Radio Buttons */}
          <div className="flex items-center gap-4 bg-slate-950/80 px-4 py-2 rounded-xl border border-slate-800">
            {SOURCES.map((src) => (
              <label key={src.id} className="flex items-center gap-2 text-xs font-semibold cursor-pointer">
                <input
                  type="radio"
                  name="sourceType"
                  value={src.id}
                  checked={selectedSource === src.id}
                  onChange={() => {
                    setSelectedSource(src.id)
                    setUploadError(null)
                    setLastResult(null)
                  }}
                  className="accent-indigo-500 w-3.5 h-3.5 cursor-pointer"
                />
                <span className={selectedSource === src.id ? 'text-indigo-300' : 'text-slate-400'}>
                  {src.label}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Source Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 pt-1">
          {SOURCES.map((src) => {
            const isSelected = selectedSource === src.id
            return (
              <button
                key={src.id}
                type="button"
                onClick={() => {
                  setSelectedSource(src.id)
                  setLastResult(null)
                  setUploadError(null)
                }}
                className={`p-4 rounded-xl text-left border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-indigo-950/30 border-indigo-500/60 shadow-md shadow-indigo-500/10 ring-1 ring-indigo-500/40'
                    : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700 opacity-80 hover:opacity-100'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl">{src.icon}</span>
                  <span className="text-[10px] font-mono text-slate-400">{src.endpoint}</span>
                </div>
                <div className="font-bold text-sm text-white mb-0.5">{src.title}</div>
                <div className="text-xs text-slate-400 leading-snug">{src.desc}</div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Upload Zone & Configuration */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
        {/* Merchant Dropdown Selector */}
        <div className="max-w-md">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-1.5">
            Target Merchant (Optional)
          </label>
          <select
            value={merchantId}
            onChange={(e) => setMerchantId(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="">Platform-wide / All Merchants (Default)</option>
            {merchants.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} {m.business_name ? `(${m.business_name})` : ''}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-400 mt-1">
            Choose a specific merchant or leave as platform-wide to apply automatically.
          </p>
        </div>

        {/* Drag & Drop Zone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 sm:p-10 text-center cursor-pointer transition-all ${
            dragActive
              ? 'border-indigo-400 bg-indigo-950/30'
              : selectedFile
              ? 'border-indigo-500/50 bg-indigo-950/10 hover:border-indigo-400'
              : 'border-slate-800 bg-slate-950/40 hover:border-slate-700'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileChange}
            className="hidden"
          />

          {!selectedFile ? (
            <div>
              <div className="text-4xl mb-3">📁</div>
              <p className="font-semibold text-sm sm:text-base text-slate-200 mb-1">
                Select or drag and drop financial export file
              </p>
              <p className="text-xs text-slate-400">
                Supports CSV, XLSX, and XLS up to 10 MB
              </p>
            </div>
          ) : (
            <div className="space-y-3" onClick={(e) => e.stopPropagation()}>
              <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 flex items-center justify-center text-xl mx-auto shadow-md">
                📄
              </div>
              <div>
                <p className="text-xs uppercase font-bold text-indigo-400 tracking-wider">Selected File</p>
                <p className="font-bold text-base text-white mt-0.5">{selectedFile.name}</p>
                <p className="text-xs text-slate-400 mt-0.5">
                  Size: {(selectedFile.size / 1024).toFixed(1)} KB ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                </p>
              </div>

              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="px-6 py-2.5 rounded-xl font-bold text-xs text-white bg-indigo-600 hover:bg-indigo-500 transition-all disabled:opacity-50 cursor-pointer shadow-lg shadow-indigo-600/25 flex items-center gap-2"
                >
                  {isUploading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <span>⬆️</span>
                      <span>Upload File</span>
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={handleClearFile}
                  disabled={isUploading}
                  className="px-4 py-2.5 rounded-xl font-medium text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-all cursor-pointer"
                >
                  Choose Different File
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Upload Progress Indicator */}
        {isUploading && (
          <div className="space-y-2 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="flex justify-between text-xs text-slate-300 font-medium">
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
                Uploading & parsing records on server...
              </span>
              <span className="font-mono text-indigo-400 font-bold">{uploadProgress}%</span>
            </div>
            <div className="w-full h-2 rounded-full overflow-hidden bg-slate-800">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-300 rounded-full"
                style={{ width: `${Math.max(uploadProgress, 5)}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Notification */}
        {uploadError && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-start justify-between gap-3 animate-fadeIn">
            <div className="flex items-start gap-2.5">
              <span className="text-base leading-none">⚠️</span>
              <div>
                <p className="font-bold text-red-200">Upload failed</p>
                <p className="mt-0.5 text-red-300 leading-relaxed">{uploadError}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setUploadError(null)}
              className="text-red-400 hover:text-white text-base font-bold cursor-pointer"
            >
              &times;
            </button>
          </div>
        )}
      </div>

      {/* Upload Result Summary (STEP 13) */}
      {lastResult && (
        <div className="p-6 rounded-2xl bg-slate-900/70 border border-emerald-500/30 space-y-4 shadow-xl shadow-emerald-500/5 animate-fadeIn">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="text-lg">✅</span>
              <div>
                <h3 className="text-sm font-bold text-emerald-300">Upload successful</h3>
                <p className="text-xs text-slate-400">
                  File <span className="text-slate-200 font-semibold">{lastResult.file_name}</span> processed as{' '}
                  <span className="capitalize font-mono text-indigo-400 font-semibold">{lastResult.source}</span>
                </p>
              </div>
            </div>
            <StatusBadge status={lastResult.status} />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-bold">Total rows</div>
              <div className="text-2xl font-black text-slate-100 mt-1">{lastResult.total_rows}</div>
            </div>
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30">
              <div className="text-[10px] text-emerald-400 uppercase font-bold">Imported rows</div>
              <div className="text-2xl font-black text-emerald-300 mt-1">{lastResult.imported_rows}</div>
            </div>
            <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/30">
              <div className="text-[10px] text-amber-400 uppercase font-bold">Duplicate rows</div>
              <div className="text-2xl font-black text-amber-300 mt-1">{lastResult.duplicate_rows}</div>
            </div>
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30">
              <div className="text-[10px] text-rose-400 uppercase font-bold">Invalid rows</div>
              <div className="text-2xl font-black text-rose-300 mt-1">{lastResult.invalid_rows}</div>
            </div>
          </div>

          {/* Validation Warnings/Errors List if present */}
          {lastResult.errors && lastResult.errors.length > 0 && (
            <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <p className="text-xs font-bold text-amber-300 uppercase tracking-wide">
                Row-Level Validation Notices ({lastResult.errors.length})
              </p>
              <div className="max-h-40 overflow-y-auto divide-y divide-slate-900 text-xs text-slate-400">
                {lastResult.errors.map((err, i) => (
                  <div key={i} className="py-1.5 flex items-center justify-between gap-2">
                    <span>Row {err.row_number} [{err.field}]: {err.error}</span>
                    {err.raw_value && <span className="font-mono text-[10px] text-slate-400 truncate max-w-[200px]">{String(err.raw_value)}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* History Table */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white">Import Batch History</h3>
            <p className="text-xs text-slate-400">Log of all historical file ingestion attempts</p>
          </div>
          <button
            type="button"
            onClick={fetchHistory}
            disabled={loadingHistory}
            className="text-xs px-3.5 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 transition-colors cursor-pointer flex items-center gap-1.5"
          >
            <span>🔄</span>
            <span>{loadingHistory ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] font-semibold tracking-wider">
                <th className="py-2.5 px-3">File Name</th>
                <th className="py-2.5 px-3">Source</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Imported</th>
                <th className="py-2.5 px-3">Duplicates</th>
                <th className="py-2.5 px-3">Invalid</th>
                <th className="py-2.5 px-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {history.map((batch) => (
                <tr key={batch.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-3 font-semibold text-slate-200">{batch.file_name}</td>
                  <td className="py-3 px-3 capitalize text-slate-300 font-mono text-[11px]">{batch.source}</td>
                  <td className="py-3 px-3">
                    <StatusBadge status={batch.status} size="xs" />
                  </td>
                  <td className="py-3 px-3 font-bold text-emerald-400">{batch.imported_rows}</td>
                  <td className="py-3 px-3 text-amber-400">{batch.duplicate_rows}</td>
                  <td className="py-3 px-3 text-rose-400">{batch.invalid_rows}</td>
                  <td className="py-3 px-3 text-slate-400">{formatDateTime(batch.created_at)}</td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No import batches logged yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
