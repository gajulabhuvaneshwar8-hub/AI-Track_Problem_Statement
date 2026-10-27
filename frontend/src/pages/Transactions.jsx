import React, { useState, useEffect } from 'react'
import PageHeader from '../components/layout/PageHeader'
import DataTable from '../components/common/DataTable'
import StatusBadge from '../components/common/StatusBadge'
import Modal from '../components/common/Modal'
import { transactionService } from '../services/transactionService'
import { formatCurrency, formatDateTime, truncateId } from '../utils/formatters'

export default function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)

  // Filters
  const [statusFilter, setStatusFilter] = useState('')
  const [gatewayFilter, setGatewayFilter] = useState('')

  // Selected Transaction for Modal
  const [selectedTxn, setSelectedTxn] = useState(null)

  const fetchTransactions = async () => {
    try {
      setLoading(true)
      const params = {
        page,
        page_size: pageSize,
      }
      if (statusFilter) params.status = statusFilter
      if (gatewayFilter) params.gateway = gatewayFilter

      const res = await transactionService.listTransactions(params)
      setTransactions(res.items || [])
      setTotal(res.total || 0)
    } catch (err) {
      console.error('Failed to load transactions:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTransactions()
  }, [page, statusFilter, gatewayFilter])

  const columns = [
    {
      header: 'Reference / ID',
      accessor: 'reference_id',
      render: (val, row) => (
        <div>
          <span className="font-mono font-medium text-slate-200">{val || truncateId(row.id)}</span>
          <p className="text-[10px] text-slate-500 font-mono">{truncateId(row.id)}</p>
        </div>
      ),
    },
    {
      header: 'Source & Gateway',
      accessor: 'gateway',
      render: (val, row) => (
        <div>
          <span className="font-semibold text-slate-300 capitalize">{val || 'Direct'}</span>
          <p className="text-[10px] text-slate-400 capitalize">{row.source ? String(row.source).replace(/_/g, ' ') : 'Gateway'}</p>
        </div>
      ),
    },
    {
      header: 'Amount',
      accessor: 'amount',
      render: (val, row) => (
        <span className="font-bold text-slate-100">
          {formatCurrency(val, row.currency)}
        </span>
      ),
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (val) => <StatusBadge status={val} size="xs" />,
    },
    {
      header: 'Payment Method',
      accessor: 'payment_method',
      render: (val) => <span className="capitalize text-slate-300">{val || 'Card'}</span>,
    },
    {
      header: 'Timestamp',
      accessor: 'created_at',
      render: (val) => <span className="text-slate-400">{formatDateTime(val)}</span>,
    },
    {
      header: 'Action',
      accessor: 'id',
      className: 'text-right',
      render: (_, row) => (
        <button
          onClick={(e) => {
            e.stopPropagation()
            setSelectedTxn(row)
          }}
          className="px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
        >
          View Details
        </button>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Transactions Ledger"
        subtitle="All incoming internal and gateway transactions recorded across financial rails"
      />

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
              Status Filter
            </label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="success">Success</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
              <option value="refunded">Refunded</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
              Gateway
            </label>
            <select
              value={gatewayFilter}
              onChange={(e) => {
                setGatewayFilter(e.target.value)
                setPage(1)
              }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Gateways</option>
              <option value="stripe">Stripe</option>
              <option value="razorpay">Razorpay</option>
              <option value="paypal">PayPal</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-slate-400">
          Showing total <strong className="text-slate-200">{total}</strong> transactions
        </div>
      </div>

      {/* Transactions Data Table */}
      <DataTable
        columns={columns}
        data={transactions}
        loading={loading}
        onRowClick={(row) => setSelectedTxn(row)}
        pagination={{
          page,
          pageSize,
          total,
          onPageChange: (newPage) => setPage(newPage),
        }}
        emptyTitle="No Transactions Found"
        emptyMessage="Try clearing or adjusting your status/gateway filters."
      />

      {/* Detail Modal */}
      <Modal
        isOpen={Boolean(selectedTxn)}
        onClose={() => setSelectedTxn(null)}
        title="Transaction Details"
        subtitle={`ID: ${selectedTxn?.id}`}
        maxWidth="max-w-2xl"
        footer={
          <button
            onClick={() => setSelectedTxn(null)}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200"
          >
            Close
          </button>
        }
      >
        {selectedTxn && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div>
                <span className="text-slate-400 block mb-1">Transaction Reference</span>
                <span className="font-mono font-bold text-slate-100">{selectedTxn.reference_id || '—'}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Status</span>
                <StatusBadge status={selectedTxn.status} />
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Amount & Currency</span>
                <span className="font-bold text-slate-100 text-base">
                  {formatCurrency(selectedTxn.amount, selectedTxn.currency)}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Fee Amount</span>
                <span className="text-slate-300">
                  {formatCurrency(selectedTxn.fee_amount, selectedTxn.currency)}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Gateway & Source</span>
                <span className="text-slate-200 capitalize">
                  {selectedTxn.gateway || 'None'} ({selectedTxn.source})
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Payment Method</span>
                <span className="text-slate-200 capitalize">{selectedTxn.payment_method || '—'}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Created At</span>
                <span className="text-slate-300">{formatDateTime(selectedTxn.created_at)}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Merchant ID</span>
                <span className="font-mono text-slate-300">{truncateId(selectedTxn.merchant_id)}</span>
              </div>
            </div>

            {selectedTxn.raw_data && (
              <div>
                <span className="text-slate-400 font-semibold block mb-1.5">Raw Payload Metadata</span>
                <pre className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 font-mono text-[11px] text-slate-300 overflow-x-auto max-h-48">
                  {JSON.stringify(selectedTxn.raw_data, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
