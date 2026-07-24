import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export const DASHBOARD_ROOT = path.resolve(__dirname, '..')
export const PROJECT_ROOT = path.resolve(DASHBOARD_ROOT, '..')
export const RESULT_DIR = path.join(PROJECT_ROOT, 'Result')
export const QS_LOGO_DIR = path.join(PROJECT_ROOT, 'QSLogo')
export const PYTHON_EXECUTABLE = process.env.PYTHON_EXECUTABLE || 'python'

export const RESULT_FILE_NAMES = [
  'QSRank.txt',
  'Lianjia.xls',
  'Lianjia.xlsx',
  'Lianjia_Public.xls',
  'Lianjia_Public.xlsx',
  'Lianjia_Login.xls',
  'Lianjia_Login.xlsx',
] as const

