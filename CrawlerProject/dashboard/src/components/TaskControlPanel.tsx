import { LoaderCircle, PauseCircle, PlayCircle, FolderOpen } from 'lucide-react'
import type { RunTaskForm, TaskRuntimeState } from '@/types/dashboard'

interface TaskControlPanelProps {
  form: RunTaskForm
  status: TaskRuntimeState
  loading: boolean
  onChange: (patch: Partial<RunTaskForm>) => void
  onRun: () => void
  onStop: () => void
  onOpenDirectory: () => void
}

export function TaskControlPanel({
  form,
  status,
  loading,
  onChange,
  onRun,
  onStop,
  onOpenDirectory,
}: TaskControlPanelProps) {
  const isLianjia = form.crawler === 'lianjia'

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-cyan-200">任务执行控制台</p>
          <h2 className="mt-2 font-serif text-2xl text-white">配置抓取参数并启动脚本</h2>
        </div>
        <div className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300">
          当前状态：{status.running ? '运行中' : '空闲'}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="任务类型">
          <select
            value={form.crawler}
            onChange={(event) => onChange({ crawler: event.target.value as RunTaskForm['crawler'] })}
          >
            <option value="qs">QS 排名抓取</option>
            <option value="lianjia">链家房源抓取</option>
          </select>
        </Field>
        <Field label="浏览器">
          <select
            value={form.browser}
            onChange={(event) => onChange({ browser: event.target.value as RunTaskForm['browser'] })}
          >
            <option value="edge">Edge</option>
            <option value="chrome">Chrome</option>
          </select>
        </Field>
        <Field label="目标房源数 / 保底 QS 条数">
          <input
            type="number"
            min={100}
            value={form.targetCount}
            onChange={(event) => onChange({ targetCount: Number(event.target.value) || 100 })}
          />
        </Field>
        <Field label="详情页抓取数">
          <input
            type="number"
            min={0}
            value={form.maxDetailPages}
            onChange={(event) => onChange({ maxDetailPages: Number(event.target.value) || 0 })}
            disabled={!isLianjia}
          />
        </Field>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <Toggle
          label="禁用人工验证码介入"
          description="链家触发验证码时不暂停等待，适合只抓公开数据的场景。"
          checked={form.disableManualVerify}
          disabled={!isLianjia}
          onChange={(checked) => onChange({ disableManualVerify: checked })}
        />
        <Toggle
          label="优先跳过登录等待"
          description="若本地 Cookie 仍有效，则直接继续执行详情页抓取。"
          checked={form.skipLoginWait}
          disabled={!isLianjia}
          onChange={(checked) => onChange({ skipLoginWait: checked })}
        />
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onRun}
          disabled={loading || status.running}
          className="inline-flex items-center gap-2 rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-medium text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-600 disabled:text-slate-300"
        >
          {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
          启动任务
        </button>
        <button
          type="button"
          onClick={onStop}
          disabled={loading || !status.running}
          className="inline-flex items-center gap-2 rounded-2xl border border-orange-400/30 bg-orange-400/10 px-5 py-3 text-sm font-medium text-orange-100 transition hover:bg-orange-400/15 disabled:cursor-not-allowed disabled:border-white/10 disabled:text-slate-500"
        >
          <PauseCircle className="h-4 w-4" />
          停止任务
        </button>
        <button
          type="button"
          onClick={onOpenDirectory}
          className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-medium text-slate-200 transition hover:bg-white/10"
        >
          <FolderOpen className="h-4 w-4" />
          打开结果目录
        </button>
      </div>
    </section>
  )
}

function Field({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <label className="block rounded-2xl border border-white/10 bg-slate-950/35 p-4">
      <span className="mb-2 block text-sm text-slate-400">{label}</span>
      <div className="[&_input]:w-full [&_input]:rounded-xl [&_input]:border [&_input]:border-white/10 [&_input]:bg-white/5 [&_input]:px-4 [&_input]:py-3 [&_input]:text-white [&_input]:outline-none [&_select]:w-full [&_select]:rounded-xl [&_select]:border [&_select]:border-white/10 [&_select]:bg-white/5 [&_select]:px-4 [&_select]:py-3 [&_select]:text-white [&_select]:outline-none">
        {children}
      </div>
    </label>
  )
}

function Toggle({
  label,
  description,
  checked,
  disabled,
  onChange,
}: {
  label: string
  description: string
  checked: boolean
  disabled?: boolean
  onChange: (checked: boolean) => void
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className="flex items-start justify-between rounded-2xl border border-white/10 bg-slate-950/35 p-4 text-left transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-50"
    >
      <div>
        <p className="text-sm text-white">{label}</p>
        <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
      </div>
      <div className={`mt-1 h-6 w-11 rounded-full p-1 transition ${checked ? 'bg-cyan-400' : 'bg-slate-700'}`}>
        <div className={`h-4 w-4 rounded-full bg-white transition ${checked ? 'translate-x-5' : ''}`} />
      </div>
    </button>
  )
}

