import React, { useState, useEffect } from 'react'
import PageHeader from '../components/layout/PageHeader'
import DataTable from '../components/common/DataTable'
import StatusBadge from '../components/common/StatusBadge'
import Modal from '../components/common/Modal'
import { settlementService } from '../services/settlementService'
import { formatCurrency, formatDateTime, formatDate, truncateId } from '../utils/formatters'

export default function Settlements() {
  const [settlements, setSettlements] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [selectedSettlement, setSelectedSettlement] = useState(null)

  const fetchSettlements = async () => {
    try {
      setLoading(true)
      const data = await settlementService.listSettlements({
        page,
        page_size: pageSize,
      })
      setSettlements(data || [])
    } catch (err) {
      console.error('Failed to load settlements:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSettlements()
  }, [page])

  // Summary figures
  const totalGross = settlements.reduce((acc, s) => acc + (Number(s.gross_amount) || 0), 0)
  const totalFees = settlements.reduce((acc, s) => acc + (Number(s.fee_amount) || 0), 0)
  const totalNet = settlements.reduce((acc, s) => acc + (Number(s.net_amount) || 0), 0)

  const columns = [
    {
      header: 'Settlement Ref / Batch',
      accessor: 'settlement_reference',
      render: (val, row) => (
        <div>
          <span className="font-mono font-medium text-slate-200">{val || truncateId(row.id)}</span>
          <p className="text-[10px] text-slate-500 font-mono">{truncateId(row.id)}</p>
        </div>
      ),
    },
    {
      header: 'Gateway',
      accessor: 'gateway',
      render: (val) => <span className="font-semibold text-slate-300 capitalize">{val || 'Bank Direct'}</span>,
    },
    {
      header: 'Gross Amount',
      accessor: 'gross_amount',
      className: 'text-right',
      render: (val, row) => (
        <span className="font-semibold text-slate-100 font-mono">
          {formatCurrency(val, row.currency)}
        </span>
      ),
    },
    {
      header: 'Deductions (Fees)',
      accessor: 'fee_amount',
      className: 'text-right',
      render: (val, row) => (
        <span className="font-mono text-amber-400">
          {formatCurrency(val, row.currency)}
        </span>
      ),
    },
    {
      header: 'Net Payout',
      accessor: 'net_amount',
      className: 'text-right',
      render: (val, row) => (
        <span className="font-bold text-emerald-400 font-mono">
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
      header: 'Settlement Date',
      accessor: 'settlement_date',
      render: (val) => <span className="text-slate-400 text-xs">{formatDate(val)}</span>,
    },
    {
      header: 'Actions',
      accessor: 'id',
      className: 'text-right',
      render: (_, row) => (
        <button
          onClick={(e) => {
            e.stopPropagation()
            setSelectedSettlement(row)
          }}
          className="px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
        >
          View Batch
        </button>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settlements Ledger"
        subtitle="Gateway processor batch payouts, interchange fee deductions, and net account deposits"
      />

      {/* Aggregate Volume KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-400">Total Gross Volume</span>
          <div className="text-2xl font-bold text-white mt-1">{formatCurrency(totalGross)}</div>
          <span className="text-[10px] text-slate-500">Gross processed in view</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-400">Gateway Fees Deducted</span>
          <div className="text-2xl font-bold text-amber-400 mt-1">{formatCurrency(totalFees)}</div>
          <span className="text-[10px] text-slate-500">Processing interchange fees</span>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-400">Total Net Payouts</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{formatCurrency(totalNet)}</div>
          <span className="text-[10px] text-slate-500">Deposited into bank accounts</span>
        </div>
      </div>

      {/* Settlements Table */}
      <DataTable
        columns={columns}
        data={settlements}
        loading={loading}
        onRowClick={(row) => setSelectedSettlement(row)}
        emptyTitle="No Settlements Recorded"
        emptyMessage="No settlement batches recorded. Ingest processor settlement files to view batches."
      />

      {/* Detail Modal */}
      <Modal
        isOpen={Boolean(selectedSettlement)}
        onClose={() => setSelectedSettlement(null)}
        title="Settlement Batch Details"
        subtitle={`Reference: ${selectedSettlement?.settlement_reference || selectedSettlement?.id}`}
        footer={
          <button
            onClick={() => setSelectedSettlement(null)}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200"
          >
            Close
          </button>
        }
      >
        {selectedSettlement && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div>
                <span className="text-slate-400 block mb-1">Batch Reference</span>
                <span className="font-mono font-bold text-slate-200">
                  {selectedSettlement.settlement_reference || '—'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Status</span>
                <StatusBadge status={selectedSettlement.status} />
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Gross Amount</span>
                <span className="font-bold text-slate-100 font-mono text-sm">
                  {formatCurrency(selectedSettlement.gross_amount, selectedSettlement.currency)}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Fee Amount</span>
                <span className="font-mono text-amber-400">
                  {formatCurrency(selectedSettlement.fee_amount, selectedSettlement.currency)}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Net Payout</span>
                <span className="font-mono text-emerald-400 font-bold text-sm">
                  {formatCurrency(selectedSettlement.net_amount, selectedSettlement.currency)}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Gateway</span>
                <span className="font-semibold text-slate-200 capitalize">{selectedSettlement.gateway}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Settlement Date</span>
                <span className="text-slate-300">{formatDate(selectedSettlement.settlement_date)}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-1">Recorded At</span>
                <span className="text-slate-300">{formatDateTime(selectedSettlement.created_at)}</span>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
