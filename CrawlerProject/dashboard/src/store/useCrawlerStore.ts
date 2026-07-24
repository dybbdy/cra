import { create } from 'zustand'
import type {
  LianjiaLoginRecord,
  LianjiaPublicRecord,
  OverviewResponse,
  QsRecord,
  ResultFileItem,
  RunTaskForm,
  RuntimeLog,
  StreamEvent,
  TaskRuntimeState,
} from '@/types/dashboard'
import { requestJson } from '@/utils/api'

interface CrawlerState {
  overview: OverviewResponse | null
  taskStatus: TaskRuntimeState
  logs: RuntimeLog[]
  qsRecords: QsRecord[]
  lianjiaPublicRecords: LianjiaPublicRecord[]
  lianjiaLoginRecords: LianjiaLoginRecord[]
  resultFiles: ResultFileItem[]
  form: RunTaskForm
  loading: boolean
  streamConnected: boolean
  errorMessage: string
  loadOverview: () => Promise<void>
  loadResults: () => Promise<void>
  runTask: () => Promise<void>
  stopTask: () => Promise<void>
  openResultDirectory: () => Promise<void>
  setForm: (patch: Partial<RunTaskForm>) => void
  clearLogs: () => void
  connectStream: () => void
  disconnectStream: () => void
}

const defaultStatus: TaskRuntimeState = {
  running: false,
  crawler: null,
  startedAt: null,
  pid: null,
}

const defaultForm: RunTaskForm = {
  crawler: 'qs',
  browser: 'edge',
  targetCount: 100,
  maxDetailPages: 30,
  disableManualVerify: false,
  skipLoginWait: false,
}

let eventSource: EventSource | null = null

export const useCrawlerStore = create<CrawlerState>((set, get) => ({
  overview: null,
  taskStatus: defaultStatus,
  logs: [],
  qsRecords: [],
  lianjiaPublicRecords: [],
  lianjiaLoginRecords: [],
  resultFiles: [],
  form: defaultForm,
  loading: false,
  streamConnected: false,
  errorMessage: '',

  async loadOverview() {
    const overview = await requestJson<OverviewResponse>('/api/overview')
    set({
      overview,
      taskStatus: overview.taskStatus,
      resultFiles: overview.resultFiles,
      errorMessage: '',
    })
  },

  async loadResults() {
    const [qsRecords, lianjiaPublicRecords, lianjiaLoginRecords, resultFiles] =
      await Promise.all([
        requestJson<QsRecord[]>('/api/results/qs'),
        requestJson<LianjiaPublicRecord[]>('/api/results/lianjia/public'),
        requestJson<LianjiaLoginRecord[]>('/api/results/lianjia/login'),
        requestJson<ResultFileItem[]>('/api/files'),
      ])

    set({
      qsRecords,
      lianjiaPublicRecords,
      lianjiaLoginRecords,
      resultFiles,
      errorMessage: '',
    })
  },

  async runTask() {
    set({ loading: true, errorMessage: '' })
    try {
      await requestJson('/api/tasks/run', {
        method: 'POST',
        body: JSON.stringify(get().form),
      })
      await get().loadOverview()
    } catch (error) {
      set({
        errorMessage: error instanceof Error ? error.message : '启动任务失败',
      })
    } finally {
      set({ loading: false })
    }
  },

  async stopTask() {
    set({ loading: true, errorMessage: '' })
    try {
      await requestJson('/api/tasks/stop', {
        method: 'POST',
      })
    } catch (error) {
      set({
        errorMessage: error instanceof Error ? error.message : '停止任务失败',
      })
    } finally {
      set({ loading: false })
    }
  },

  async openResultDirectory() {
    try {
      await requestJson('/api/files/open-directory', {
        method: 'POST',
      })
    } catch (error) {
      set({
        errorMessage: error instanceof Error ? error.message : '打开目录失败',
      })
    }
  },

  setForm(patch) {
    set((state) => ({
      form: {
        ...state.form,
        ...patch,
      },
    }))
  },

  clearLogs() {
    set({ logs: [] })
  },

  connectStream() {
    if (eventSource) {
      return
    }

    eventSource = new EventSource('/api/tasks/log-stream')
    eventSource.onopen = () => {
      set({ streamConnected: true })
    }

    eventSource.onmessage = (event) => {
      const payload = JSON.parse(event.data) as StreamEvent
      if (payload.type === 'status') {
        set({ taskStatus: payload.payload })
        return
      }

      set((state) => ({
        logs: [...state.logs, payload.payload].slice(-240),
      }))
    }

    eventSource.onerror = () => {
      set({ streamConnected: false })
    }
  },

  disconnectStream() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    set({ streamConnected: false })
  },
}))
