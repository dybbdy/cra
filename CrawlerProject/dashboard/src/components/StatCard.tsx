import type { ReactNode } from 'react'

interface StatCardProps {
  title: string
  value: string
  hint: string
  accent?: 'cyan' | 'orange'
  icon: ReactNode
}

export function StatCard({ title, value, hint, accent = 'cyan', icon }: StatCardProps) {
  const tone =
    accent === 'cyan'
      ? 'border-cyan-400/20 bg-cyan-400/10 text-cyan-200'
      : 'border-orange-400/20 bg-orange-400/10 text-orange-200'

  return (
    <div className="rounded-[28px] border border-white/10 bg-white/5 p-6 shadow-xl shadow-slate-950/25 backdrop-blur">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="mt-3 font-serif text-3xl text-white">{value}</p>
        </div>
        <div className={`rounded-2xl border px-3 py-3 ${tone}`}>{icon}</div>
      </div>
      <p className="text-sm leading-6 text-slate-400">{hint}</p>
    </div>
  )
}

