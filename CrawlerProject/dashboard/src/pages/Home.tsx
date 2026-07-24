import { useEffect } from 'react'
import { ArrowRight, FolderKanban, GraduationCap, House } from 'lucide-react'
import { Link } from 'react-router-dom'
import { StatCard } from '@/components/StatCard'
import { useCrawlerStore } from '@/store/useCrawlerStore'
import { formatDateTime } from '@/utils/api'

export default function Home() {
  const overview = useCrawlerStore((state) => state.overview)
  const loadOverview = useCrawlerStore((state) => state.loadOverview)

  useEffect(() => {
    void loadOverview()
  }, [loadOverview])

  return (
    <div className="space-y-6">
      <section className="rounded-[32px] border border-white/10 bg-white/5 p-8 shadow-2xl shadow-cyan-950/20 backdrop-blur">
        <p className="text-sm uppercase tracking-[0.3em] text-cyan-200">Crawler Dashboard</p>
        <h1 className="mt-4 max-w-3xl font-serif text-4xl leading-tight text-white md:text-5xl">
          用一个可视化控制台，统一管理 QS 排名与链家房源抓取流程。
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-8 text-slate-300">
          启动本地 Python 爬虫、观察实时日志、预览结果文件、下载实验输出，适合课程展示与调试演示。
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            to="/tasks"
            className="inline-flex items-center gap-2 rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-medium text-slate-950 transition hover:bg-cyan-300"
          >
            进入任务执行页
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            to="/results"
            className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-medium text-slate-100 transition hover:bg-white/10"
          >
            查看结果文件
          </Link>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-3">
        <StatCard
          title="结果文件数"
          value={String(overview?.stats.resultFileCount ?? 0)}
          hint="已检测到 Result 目录下的任务输出文件数量。"
          icon={<FolderKanban className="h-5 w-5" />}
        />
        <StatCard
          title="QS Logo 文件数"
          value={String(overview?.stats.qsLogoCount ?? 0)}
          hint="可用于课程展示的大学 Logo 下载数量。"
          icon={<GraduationCap className="h-5 w-5" />}
        />
        <StatCard
          title="最近任务"
          value={overview?.latestTask === 'lianjia' ? '链家房源' : overview?.latestTask === 'qs' ? 'QS 排名' : '暂无'}
          hint={`最近更新时间：${formatDateTime(overview?.resultFiles[0]?.updatedAt)}`}
          accent="orange"
          icon={<House className="h-5 w-5" />}
        />
      </section>

      <section className="rounded-[28px] border border-white/10 bg-white/5 p-6 backdrop-blur">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="font-serif text-2xl text-white">最近结果摘要</h2>
            <p className="mt-2 text-sm text-slate-400">展示最近生成的结果文件，便于快速检查实验产出。</p>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {(overview?.resultFiles || []).slice(0, 4).map((file) => (
            <div key={file.name} className="rounded-2xl border border-white/10 bg-slate-950/35 p-4">
              <p className="text-sm text-slate-400">{file.name}</p>
              <p className="mt-2 text-lg text-white">{formatDateTime(file.updatedAt)}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
