import React from 'react'

export default function LoadingSpinner({ message = 'Loading data...', size = 'md', className = '' }) {
  const spinnerSize = size === 'sm' ? 'w-4 h-4 border-2' : size === 'lg' ? 'w-10 h-10 border-3' : 'w-6 h-6 border-2'

  return (
    <div className={`flex flex-col items-center justify-center p-8 gap-3 text-slate-400 ${className}`}>
      <div
        className={`${spinnerSize} border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin`}
      />
      {message && <p className="text-xs font-medium tracking-wide text-slate-400">{message}</p>}
    </div>
  )
}
