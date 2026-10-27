import React, { useState, useEffect } from 'react'
import PageHeader from '../components/layout/PageHeader'
import DataTable from '../components/common/DataTable'
import Modal from '../components/common/Modal'
import { merchantService } from '../services/merchantService'
import { formatDateTime, truncateId } from '../utils/formatters'

export default function Merchants() {
  const [merchants, setMerchants] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedMerchant, setSelectedMerchant] = useState(null)

  // Registration Modal
  const [isRegisterOpen, setIsRegisterOpen] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    country: 'IN',
    currency: 'INR',
    settlement_cycle: 'T+1',
  })
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)

  const fetchMerchants = async () => {
    try {
      setLoading(true)
      const data = await merchantService.listMerchants()
      setMerchants(data || [])
    } catch (err) {
      console.error('Failed to load merchants:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMerchants()
  }, [])

  const handleRegisterSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    try {
      setSubmitting(true)
      await merchantService.createMerchant(formData)
      setIsRegisterOpen(false)
      setFormData({
        name: '',
        email: '',
        country: 'IN',
        currency: 'INR',
        settlement_cycle: 'T+1',
      })
      await fetchMerchants()
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to register merchant.')
    } finally {
      setSubmitting(false)
    }
  }

  const columns = [
    {
      header: 'Business Name',
      accessor: 'name',
      render: (val, row) => (
        <div>
          <span className="font-semibold text-slate-100">{val}</span>
          <p className="text-[10px] text-slate-500 font-mono">{truncateId(row.id)}</p>
        </div>
      ),
    },
    {
      header: 'Contact Email',
      accessor: 'email',
      render: (val) => <span className="text-slate-300">{val}</span>,
    },
    {
      header: 'Country',
      accessor: 'country',
      render: (val) => <span className="font-mono text-slate-300">{val}</span>,
    },
    {
      header: 'Currency',
      accessor: 'currency',
      render: (val) => (
        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-800 text-indigo-300 border border-slate-700">
          {val}
        </span>
      ),
    },
    {
      header: 'Settlement Cycle',
      accessor: 'settlement_cycle',
      render: (val) => <span className="text-slate-300 font-mono">{val || 'T+1'}</span>,
    },
    {
      header: 'Onboarded At',
      accessor: 'created_at',
      render: (val) => <span className="text-slate-400 text-[11px]">{formatDateTime(val)}</span>,
    },
    {
      header: 'Actions',
      accessor: 'id',
      className: 'text-right',
      render: (_, row) => (
        <button
          onClick={(e) => {
            e.stopPropagation()
            setSelectedMerchant(row)
          }}
          className="px-2.5 py-1 text-[11px] font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
        >
          View Profile
        </button>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Merchants Directory"
        subtitle="Configured merchant entities, account currencies, and settlement cycle configurations"
        actions={
          <button
            onClick={() => setIsRegisterOpen(true)}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-1.5"
          >
            <span>+</span>
            <span>Register Merchant</span>
          </button>
        }
      />

      <DataTable
        columns={columns}
        data={merchants}
        loading={loading}
        onRowClick={(row) => setSelectedMerchant(row)}
        emptyTitle="No Merchants Registered"
        emptyMessage="Register your first merchant account to begin reconciling tenant transactions."
      />

      {/* Merchant Profile Modal */}
      <Modal
        isOpen={Boolean(selectedMerchant)}
        onClose={() => setSelectedMerchant(null)}
        title="Merchant Account Profile"
        subtitle={`ID: ${selectedMerchant?.id}`}
        footer={
          <button
            onClick={() => setSelectedMerchant(null)}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200"
          >
            Close
          </button>
        }
      >
        {selectedMerchant && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div>
                <span className="text-slate-400 block mb-1">Business Name</span>
                <span className="font-bold text-white text-sm">{selectedMerchant.name}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Email Address</span>
                <span className="text-slate-200">{selectedMerchant.email}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Settlement Cycle</span>
                <span className="font-mono text-indigo-400 font-semibold">{selectedMerchant.settlement_cycle}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Default Currency</span>
                <span className="font-mono font-bold text-slate-200">{selectedMerchant.currency}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Jurisdiction / Country</span>
                <span className="text-slate-200">{selectedMerchant.country}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Registration Date</span>
                <span className="text-slate-300">{formatDateTime(selectedMerchant.created_at)}</span>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Registration Modal */}
      <Modal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        title="Register New Merchant"
        subtitle="Onboard a new merchant partner for multi-tenant reconciliation"
        footer={
          <div className="flex items-center justify-end gap-2 w-full">
            <button
              type="button"
              onClick={() => setIsRegisterOpen(false)}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              form="merchant-register-form"
              disabled={submitting}
              className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50"
            >
              {submitting ? 'Registering...' : 'Register Merchant'}
            </button>
          </div>
        }
      >
        <form id="merchant-register-form" onSubmit={handleRegisterSubmit} className="space-y-3.5 text-xs">
          {formError && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-xs">
              {formError}
            </div>
          )}

          <div>
            <label className="block text-slate-400 font-medium mb-1">Business Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Acme Payments India Ltd"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-slate-400 font-medium mb-1">Contact Email</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="finance@acme.com"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-slate-400 font-medium mb-1">Country</label>
              <input
                type="text"
                required
                maxLength={2}
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value.toUpperCase() })}
                placeholder="IN"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500 uppercase font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Currency</label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="INR">INR (₹)</option>
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-400 font-medium mb-1">Cycle</label>
              <select
                value={formData.settlement_cycle}
                onChange={(e) => setFormData({ ...formData, settlement_cycle: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="T+1">T+1</option>
                <option value="T+2">T+2</option>
                <option value="T+0">T+0 (Instant)</option>
              </select>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  )
}
