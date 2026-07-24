import { BarChart3, Command, Files, House, Sparkles } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: '总览', icon: House },
  { to: '/tasks', label: '任务执行', icon: Command },
  { to: '/results', label: '结果查看', icon: Files },
]

export function AppShell() {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.15),_transparent_35%),linear-gradient(180deg,_#081121_0%,_#091827_38%,_#06101a_100%)] text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-[1600px] gap-8 px-6 py-6 lg:px-8">
        <aside className="hidden w-72 shrink-0 flex-col rounded-[28px] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-cyan-950/25 backdrop-blur xl:flex">
          <div className="mb-10 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-400/15 text-cyan-300">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <p className="font-serif text-xl tracking-wide text-white">Crawler Console</p>
              <p className="text-sm text-slate-400">课程实验可视化控制台</p>
            </div>
          </div>

          <nav className="space-y-2">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition ${
                    isActive
                      ? 'bg-cyan-400/15 text-cyan-200 shadow-lg shadow-cyan-900/20'
                      : 'text-slate-300 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="mt-auto rounded-3xl border border-white/10 bg-slate-950/40 p-5">
            <div className="mb-3 flex items-center gap-2 text-sm text-cyan-200">
              <BarChart3 className="h-4 w-4" />
              <span>运行策略</span>
            </div>
            <p className="text-sm leading-6 text-slate-400">
              前端控制台仅负责启动本地 Python 脚本、订阅日志流与展示结果文件，不改动你的爬虫核心逻辑。
            </p>
          </div>
        </aside>

        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

