import React, { useState } from 'react'
import { Check, ChevronDown, Loader2, User, UserMinus, UserPlus } from '../common/Icons'

export default function AssignmentControl({
  currentAssigneeId,
  currentAssigneeName,
  assignees = [],
  onAssign,
  disabled = false,
  size = 'md',
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)

  const handleSelect = async (userId) => {
    if (userId === currentAssigneeId) {
      setIsOpen(false)
      return
    }
    try {
      setIsUpdating(true)
      await onAssign(userId)
      setIsOpen(false)
    } catch (err) {
      console.error('Failed to assign user:', err)
    } finally {
      setIsUpdating(false)
    }
  }

  const isAssigned = Boolean(currentAssigneeId)

  return (
    <div className="relative inline-block text-left">
      <button
        type="button"
        disabled={disabled || isUpdating}
        onClick={() => setIsOpen(!isOpen)}
        className={`inline-flex items-center gap-2 rounded-lg border transition-all ${
          isAssigned
            ? 'bg-slate-800/80 border-slate-700/80 text-slate-200 hover:border-slate-600 hover:bg-slate-800'
            : 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/20'
        } ${
          size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-xs font-medium'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
        title={isAssigned ? `Assigned to ${currentAssigneeName}` : 'Assign to operator'}
      >
        {isUpdating ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
        ) : isAssigned ? (
          <User className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
        ) : (
          <UserPlus className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
        )}

        <span className="truncate max-w-[140px]">
          {isAssigned ? currentAssigneeName : 'Unassigned'}
        </span>

        {!disabled && <ChevronDown className="w-3 h-3 text-slate-400 shrink-0 ml-0.5" />}
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-1.5 w-60 rounded-xl bg-slate-900 border border-slate-700/80 shadow-2xl shadow-black/60 z-50 py-1.5 backdrop-blur-xl animate-in fade-in zoom-in-95 duration-100">
            <div className="px-3 py-1.5 text-[11px] font-semibold tracking-wider text-slate-400 uppercase border-b border-slate-800 mb-1">
              Assign Exception Ticket
            </div>

            {isAssigned && (
              <button
                type="button"
                onClick={() => handleSelect(null)}
                className="w-full text-left px-3 py-2 text-xs flex items-center gap-2 text-rose-400 hover:bg-rose-500/10 transition-colors"
              >
                <UserMinus className="w-3.5 h-3.5" />
                <span>Unassign Ticket</span>
              </button>
            )}

            <div className="max-h-52 overflow-y-auto py-0.5">
              {assignees.length === 0 ? (
                <div className="px-3 py-2 text-xs text-slate-500 italic">
                  No active operators found
                </div>
              ) : (
                assignees.map((user) => {
                  const selected = user.id === currentAssigneeId
                  return (
                    <button
                      key={user.id}
                      type="button"
                      onClick={() => handleSelect(user.id)}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between transition-colors ${
                        selected
                          ? 'bg-indigo-600/20 text-indigo-300 font-medium'
                          : 'text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <div className="flex flex-col min-w-0 pr-2">
                        <span className="truncate font-medium">{user.name}</span>
                        <span className="truncate text-[10px] text-slate-400">{user.email}</span>
                      </div>
                      {selected && <Check className="w-4 h-4 text-indigo-400 shrink-0" />}
                    </button>
                  )
                })
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
