/**
 * LandingPage.jsx — placeholder dashboard for Step 1.
 * Full dashboard UI is built in Step 2.
 */

import { Link } from 'react-router-dom'
import HealthBadge from '../components/HealthBadge'

const FEATURE_CARDS = [
  {
    icon: '🤖',
    title: 'Autonomous AI Agent',
    desc: 'Multi-ledger evidence aggregation, deterministic decision rules (MONITOR, REVIEW, ESCALATE), and team escalation routing.',
  },
  {
    icon: '🔄',
    title: 'Automated Reconciliation',
    desc: 'Match payment records across ledgers with high-accuracy rule-based and ML-driven engines.',
  },
  {
    icon: '🧠',
    title: 'AI Exception Management',
    desc: 'LLM-powered analysis surfaces root causes and recommends resolution actions in real time.',
  },
  {
    icon: '📊',
    title: 'Anomaly Detection',
    desc: 'Scikit-learn models continuously monitor transaction patterns for statistical outliers.',
  },
]

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col" style={{ background: 'var(--color-bg-deep)' }}>

      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-8 py-4 border-b"
        style={{ borderColor: 'var(--color-border)', background: 'rgba(17,24,39,0.8)', backdropFilter: 'blur(12px)' }}>
        <div className="flex items-center gap-3">
          <span className="text-2xl">⚡</span>
          <span className="font-bold text-lg tracking-tight" style={{ color: 'var(--color-text)' }}>
            PayReconcile<span style={{ color: 'var(--color-accent)' }}>.AI</span>
          </span>
        </div>
        <HealthBadge />
      </header>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="flex flex-col items-center justify-center flex-1 text-center px-6 py-24 fade-in-up">

        {/* Badge */}
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold mb-8
                         border" style={{
          background: 'rgba(99,102,241,0.12)',
          borderColor: 'rgba(99,102,241,0.35)',
          color: 'var(--color-accent-2)',
        }}>
          <span className="pulse-ring inline-block w-2 h-2 rounded-full bg-indigo-400" />
          AI Finance Controller · Step 7 Autonomous Agent
        </span>

        {/* Headline */}
        <h1 className="text-5xl md:text-6xl font-extrabold leading-tight mb-6 gradient-text">
          AI-Powered Payment<br />Reconciliation Agent
        </h1>

        {/* Subtitle */}
        <p className="text-lg md:text-xl max-w-2xl mb-10 leading-relaxed"
           style={{ color: 'var(--color-muted)' }}>
          Automated financial reconciliation, multi-ledger evidence aggregation, deterministic decisioning, and explainable AI investigation.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-wrap gap-4 justify-center">
          <Link
            to="/agent-investigation"
            className="px-6 py-3 rounded-xl font-semibold text-white transition-all duration-200 cursor-pointer shadow-lg shadow-indigo-600/30 hover:opacity-90 flex items-center gap-2"
            style={{ background: 'linear-gradient(135deg, #6366f1, #818cf8)' }}
          >
            <span>🤖</span> AI Investigation Agent
          </Link>
          <Link
            to="/reconciliation"
            className="px-6 py-3 rounded-xl font-semibold border transition-all duration-200 hover:bg-slate-800 flex items-center gap-2 text-indigo-300"
            style={{ borderColor: 'rgba(99,102,241,0.4)', background: 'rgba(99,102,241,0.1)' }}
          >
            <span>⚡</span> Open Reconciliation
          </Link>
          <Link
            to="/ai-analysis"
            className="px-6 py-3 rounded-xl font-semibold border transition-all duration-200 hover:bg-slate-800 flex items-center gap-2 text-indigo-300"
            style={{ borderColor: 'rgba(99,102,241,0.4)', background: 'rgba(99,102,241,0.1)' }}
          >
            <span>✨</span> AI Mismatch Analysis
          </Link>
          <Link
            to="/import"
            className="px-6 py-3 rounded-xl font-semibold border transition-all duration-200 hover:bg-slate-800 flex items-center gap-2"
            style={{ borderColor: 'var(--color-border)', color: 'var(--color-text)' }}
          >
            <span>📥</span> Import Data Files
          </Link>
        </div>



        <p className="mt-4 text-xs" style={{ color: 'var(--color-muted)' }}>
          Step 1 Foundation — Full dashboard unlocked in Step 2
        </p>
      </section>

      {/* ── Feature cards ───────────────────────────────────────────────── */}
      <section className="px-8 pb-16">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURE_CARDS.map((card, i) => (
            <div
              key={i}
              className="glass-card p-6 flex flex-col gap-3 hover:border-indigo-500/40
                         transition-all duration-300 hover:-translate-y-1"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <span className="text-3xl">{card.icon}</span>
              <h3 className="font-semibold text-sm" style={{ color: 'var(--color-text)' }}>
                {card.title}
              </h3>
              <p className="text-xs leading-relaxed" style={{ color: 'var(--color-muted)' }}>
                {card.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="text-center py-6 text-xs border-t"
        style={{ borderColor: 'var(--color-border)', color: 'var(--color-muted)' }}>
        AI Payment Reconciliation Agent · Step 1 Foundation · Built with FastAPI + React + Vite
      </footer>

    </main>
  )
}
