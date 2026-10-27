import React from 'react'
import { Filter, RotateCcw, Search } from '../common/Icons'

export default function ExceptionFilters({
  filters,
  onChange,
  onReset,
  assignees = [],
  categories = [],
}) {
  const handleChange = (key, value) => {
    onChange({
      ...filters,
      [key]: value,
      page: 1, // Reset page on filter change
    })
  }

  const hasActiveFilters = Boolean(
    filters.search ||
    filters.status ||
    filters.severity ||
    filters.category ||
    filters.assigned_to
  )

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-md space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-3">
        {/* Search input */}
        <div className="lg:col-span-4 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search exceptions by title, category, description..."
            value={filters.search || ''}
            onChange={(e) => handleChange('search', e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/50 transition-all"
          />
        </div>

        {/* Status selector */}
        <div className="lg:col-span-2">
          <select
            value={filters.status || ''}
            onChange={(e) => handleChange('status', e.target.value || undefined)}
            className="w-full px-3 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500/80 transition-all"
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="ignored">Ignored</option>
          </select>
        </div>

        {/* Severity selector */}
        <div className="lg:col-span-2">
          <select
            value={filters.severity || ''}
            onChange={(e) => handleChange('severity', e.target.value || undefined)}
            className="w-full px-3 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500/80 transition-all"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Category selector */}
        <div className="lg:col-span-2">
          <select
            value={filters.category || ''}
            onChange={(e) => handleChange('category', e.target.value || undefined)}
            className="w-full px-3 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500/80 transition-all"
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>

        {/* Assignee selector */}
        <div className="lg:col-span-2">
          <select
            value={filters.assigned_to || ''}
            onChange={(e) => handleChange('assigned_to', e.target.value || undefined)}
            className="w-full px-3 py-2 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500/80 transition-all"
          >
            <option value="">All Assignees</option>
            {assignees.map((user) => (
              <option key={user.id} value={user.id}>
                {user.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {hasActiveFilters && (
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs">
          <div className="flex items-center gap-1.5 text-slate-400">
            <Filter className="w-3.5 h-3.5 text-indigo-400" />
            <span>Active filters applied</span>
          </div>
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset filters</span>
          </button>
        </div>
      )}
    </div>
  )
}
