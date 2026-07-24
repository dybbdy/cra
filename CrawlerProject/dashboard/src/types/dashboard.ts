export type CrawlerType = 'qs' | 'lianjia'
export type BrowserType = 'edge' | 'chrome'
export type LogLevel = 'info' | 'warn' | 'error' | 'system'

export interface TaskRuntimeState {
  running: boolean
  crawler: CrawlerType | null
  startedAt: string | null
  pid: number | null
}

export interface RuntimeLog {
  id: string
  level: LogLevel
  message: string
  timestamp: string
}

export interface ResultFileItem {
  name: string
  path: string
  updatedAt: string
  size: number
}

export interface OverviewResponse {
  latestTask: CrawlerType | null
  running: boolean
  taskStatus: TaskRuntimeState
  resultFiles: ResultFileItem[]
  stats: {
    resultFileCount: number
    qsLogoCount: number
  }
}

export interface RunTaskForm {
  crawler: CrawlerType
  browser: BrowserType
  targetCount: number
  maxDetailPages: number
  disableManualVerify: boolean
  skipLoginWait: boolean
}

export interface QsRecord {
  学校名称: string
  排名: string
  分数: string
  城市: string
  国家: string
  'Logo URL': string
}

export interface LianjiaPublicRecord {
  小区名: string
  户型: string
  面积: string
  朝向: string
  楼层: string
  总价: string
  单价: string
}

export interface LianjiaLoginRecord extends LianjiaPublicRecord {
  脱敏姓名: string
  电话密文: string
  HMAC: string
}

export type StreamEvent =
  | { type: 'status'; payload: TaskRuntimeState }
  | { type: 'log'; payload: RuntimeLog }

