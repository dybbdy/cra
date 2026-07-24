import { useEffect } from 'react'
import { LogConsole } from '@/components/LogConsole'
import { TaskControlPanel } from '@/components/TaskControlPanel'
import { useCrawlerStore } from '@/store/useCrawlerStore'

export default function Tasks() {
  const {
    form,
    taskStatus,
    loading,
    logs,
    streamConnected,
    errorMessage,
    setForm,
    runTask,
    stopTask,
    clearLogs,
    connectStream,
    disconnectStream,
    loadOverview,
    openResultDirectory,
  } = useCrawlerStore()

  useEffect(() => {
    connectStream()
    void loadOverview()
    return () => {
      disconnectStream()
    }
  }, [connectStream, disconnectStream, loadOverview])

  return (
    <div className="space-y-6">
      <TaskControlPanel
        form={form}
        status={taskStatus}
        loading={loading}
        onChange={setForm}
        onRun={() => void runTask()}
        onStop={() => void stopTask()}
        onOpenDirectory={() => void openResultDirectory()}
      />

      <section className="grid gap-5 xl:grid-cols-[1.3fr_0.7fr]">
        <LogConsole
          logs={logs}
          streamConnected={streamConnected}
          errorMessage={errorMessage}
          onClear={clearLogs}
        />

        <aside className="space-y-5">
          <StatusCard
            title="当前任务"
            value={taskStatus.crawler ? taskStatus.crawler.toUpperCase() : '未启动'}
            hint={taskStatus.running ? '脚本正在执行中，可实时查看日志。' : '当前没有运行中的爬虫任务。'}
          />
          <StatusCard
            title="运行 PID"
            value={taskStatus.pid ? String(taskStatus.pid) : '暂无'}
            hint="用于判断后端当前绑定的 Python 子进程。"
          />
          <StatusCard
            title="链家说明"
            value="需人工验证"
            hint="链家任务在必要时会提示你回到浏览器完成验证与登录，然后继续复用会话抓取。"
          />
        </aside>
      </section>
    </div>
  )
}

function StatusCard({
  title,
  value,
  hint,
}: {
  title: string
  value: string
  hint: string
}) {
  return (
    <div className="rounded-[28px] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p className="text-sm text-slate-400">{title}</p>
      <p className="mt-4 font-serif text-3xl text-white">{value}</p>
      <p className="mt-4 text-sm leading-7 text-slate-400">{hint}</p>
    </div>
  )
}
