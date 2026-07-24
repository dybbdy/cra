import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process'
import readline from 'node:readline'
import type { Response } from 'express'
import { PROJECT_ROOT, PYTHON_EXECUTABLE, RESULT_DIR } from '../config.js'
import type {
  RunTaskRequest,
  RuntimeLog,
  TaskRuntimeState,
} from '../types.js'

type StreamEvent =
  | { type: 'status'; payload: TaskRuntimeState }
  | { type: 'log'; payload: RuntimeLog }

export class TaskManager {
  private child: ChildProcessWithoutNullStreams | null = null
  private readonly logs: RuntimeLog[] = []
  private readonly subscribers = new Set<Response>()
  private state: TaskRuntimeState = {
    running: false,
    crawler: null,
    startedAt: null,
    pid: null,
  }

  getStatus(): TaskRuntimeState {
    return { ...this.state }
  }

  getLogs(): RuntimeLog[] {
    return [...this.logs]
  }

  subscribe(res: Response) {
    this.subscribers.add(res)
    this.sendEvent(res, { type: 'status', payload: this.getStatus() })
    for (const log of this.logs.slice(-120)) {
      this.sendEvent(res, { type: 'log', payload: log })
    }
  }

  unsubscribe(res: Response) {
    this.subscribers.delete(res)
  }

  async runTask(payload: RunTaskRequest) {
    if (this.child) {
      throw new Error('当前已有任务正在运行，请先停止后再启动新的抓取任务。')
    }

    const { script, args } = buildPythonCommand(payload)
    this.child = spawn(PYTHON_EXECUTABLE, [script, ...args], {
      cwd: PROJECT_ROOT,
      env: {
        ...process.env,
      },
      stdio: 'pipe',
      windowsHide: false,
    })

    this.state = {
      running: true,
      crawler: payload.crawler,
      startedAt: new Date().toISOString(),
      pid: this.child.pid ?? null,
    }
    this.pushStatus()
    this.pushLog('system', `已启动 ${payload.crawler.toUpperCase()} 抓取任务：python ${script} ${args.join(' ')}`.trim())

    attachLineReader(this.child.stdout, (line) => this.pushLog('info', line))
    attachLineReader(this.child.stderr, (line) => this.pushLog('error', line))

    this.child.on('close', (code) => {
      this.pushLog('system', `任务已结束，退出码：${code ?? '未知'}`)
      this.child = null
      this.state = {
        running: false,
        crawler: this.state.crawler,
        startedAt: this.state.startedAt,
        pid: null,
      }
      this.pushStatus()
    })

    this.child.on('error', (error) => {
      this.pushLog('error', `任务启动失败：${error.message}`)
      this.child = null
      this.state = {
        running: false,
        crawler: payload.crawler,
        startedAt: this.state.startedAt,
        pid: null,
      }
      this.pushStatus()
    })

    return this.getStatus()
  }

  async stopTask() {
    if (!this.child?.pid) {
      return false
    }

    this.pushLog('warn', '收到停止任务请求，正在终止 Python 进程。')
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(this.child.pid), '/t', '/f'], {
        stdio: 'ignore',
        windowsHide: true,
      })
    } else {
      this.child.kill('SIGTERM')
    }
    return true
  }

  openResultDirectory() {
    const command = process.platform === 'win32' ? 'explorer' : 'open'
    spawn(command, [RESULT_DIR], {
      stdio: 'ignore',
      detached: true,
      windowsHide: true,
    }).unref()
  }

  private pushStatus() {
    const event: StreamEvent = {
      type: 'status',
      payload: this.getStatus(),
    }
    this.broadcast(event)
  }

  private pushLog(level: RuntimeLog['level'], message: string) {
    const line = message.trim()
    if (!line) {
      return
    }

    const log: RuntimeLog = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
      level,
      message: line,
      timestamp: new Date().toISOString(),
    }
    this.logs.push(log)
    if (this.logs.length > 500) {
      this.logs.shift()
    }

    this.broadcast({ type: 'log', payload: log })
  }

  private broadcast(event: StreamEvent) {
    for (const subscriber of this.subscribers) {
      this.sendEvent(subscriber, event)
    }
  }

  private sendEvent(res: Response, event: StreamEvent) {
    res.write(`data: ${JSON.stringify(event)}\n\n`)
  }
}

function attachLineReader(stream: NodeJS.ReadableStream, onLine: (line: string) => void) {
  const lineReader = readline.createInterface({ input: stream })
  lineReader.on('line', onLine)
}

function buildPythonCommand(payload: RunTaskRequest) {
  const browser = payload.browser || 'edge'

  if (payload.crawler === 'qs') {
    return {
      script: 'qs_rank.py',
      args: ['--browser', browser],
    }
  }

  const args = [
    '--browser',
    browser,
    '--target-count',
    String(Math.max(100, payload.targetCount || 100)),
    '--max-detail-pages',
    String(Math.max(0, payload.maxDetailPages || 30)),
  ]

  if (payload.disableManualVerify) {
    args.push('--disable-manual-verify')
  }

  if (payload.skipLoginWait) {
    args.push('--skip-login-wait')
  }

  return {
    script: 'lianjia.py',
    args,
  }
}

export const taskManager = new TaskManager()

