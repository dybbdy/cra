import { TerminalSquare, Wifi, WifiOff } from 'lucide-react'
import type { RuntimeLog } from '@/types/dashboard'
import { formatDateTime } from '@/utils/api'

interface LogConsoleProps {
  logs: RuntimeLog[]
  streamConnected: boolean
  errorMessage: string
  onClear: () => void
}

const levelClassMap: Record<RuntimeLog['level'], string> = {
  info: 'text-slate-200',
  warn: 'text-orange-200',
  error: 'text-rose-200',
  system: 'text-cyan-200',
}

export function LogConsole({ logs, streamConnected, errorMessage, onClear }: LogConsoleProps) {
  return (
    <section className="rounded-[28px] border border-white/10 bg-slate-950/60 p-6 shadow-2xl shadow-cyan-950/15">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-3 text-cyan-200">
            <TerminalSquare className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-serif text-xl text-white">实时日志流</h3>
            <p className="text-sm text-slate-400">后端会持续推送 Python 标准输出与错误输出。</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300">
            {streamConnected ? <Wifi className="h-4 w-4 text-cyan-200" /> : <WifiOff className="h-4 w-4 text-orange-200" />}
            {streamConnected ? '日志通道已连接' : '日志通道未连接'}
          </span>
          <button
            type="button"
            onClick={onClear}
            className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5"
          >
            清空日志
          </button>
        </div>
      </div>

      {errorMessage ? (
        <div className="mb-4 rounded-2xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">
          {errorMessage}
        </div>
      ) : null}

      <div className="h-[440px] overflow-auto rounded-3xl border border-white/10 bg-[#030712] px-4 py-4 font-mono text-sm leading-7">
        {logs.length === 0 ? (
          <div className="flex h-full items-center justify-center text-slate-500">
            尚未收到日志，启动任务后将在这里实时显示。
          </div>
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <div key={log.id} className="grid grid-cols-[170px_1fr] gap-4 border-b border-white/5 pb-2">
                <span className="text-xs text-slate-500">{formatDateTime(log.timestamp)}</span>
                <span className={levelClassMap[log.level]}>{log.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

