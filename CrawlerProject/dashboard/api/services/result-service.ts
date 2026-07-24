import fs from 'node:fs'
import path from 'node:path'
import xlsx from 'xlsx'
import { QS_LOGO_DIR, RESULT_DIR, RESULT_FILE_NAMES } from '../config.js'
import type {
  LianjiaLoginRecord,
  LianjiaPublicRecord,
  QsRecord,
  ResultFileItem,
} from '../types.js'
import {
  normalizeLoginRows,
  normalizePublicRows,
  parseQsText,
} from '../utils/result-parser.js'

export class ResultService {
  listResultFiles(): ResultFileItem[] {
    const items = RESULT_FILE_NAMES
      .map((name) => this.buildFileItem(path.join(RESULT_DIR, name)))
      .filter((item): item is ResultFileItem => item !== null)
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))

    return items
  }

  getOverview() {
    const files = this.listResultFiles()
    return {
      latestTask: inferLatestTask(files),
      running: false,
      resultFiles: files,
      stats: {
        resultFileCount: files.length,
        qsLogoCount: countFiles(QS_LOGO_DIR),
      },
    }
  }

  getQsRecords(): QsRecord[] {
    const filePath = path.join(RESULT_DIR, 'QSRank.txt')
    if (!fs.existsSync(filePath)) {
      return []
    }
    const content = fs.readFileSync(filePath, 'utf-8')
    return parseQsText(content)
  }

  getLianjiaPublicRecords(): LianjiaPublicRecord[] {
    const filePath = this.resolveFirstExisting('Lianjia_Public.xls', 'Lianjia_Public.xlsx')
    if (!filePath) {
      return []
    }
    return normalizePublicRows(this.readSheetRows(filePath))
  }

  getLianjiaLoginRecords(): LianjiaLoginRecord[] {
    const filePath = this.resolveFirstExisting('Lianjia_Login.xls', 'Lianjia_Login.xlsx')
    if (!filePath) {
      return []
    }
    return normalizeLoginRows(this.readSheetRows(filePath))
  }

  getDownloadPath(fileName: string): string | null {
    const target = RESULT_FILE_NAMES.find((name) => name === fileName)
    if (!target) {
      return null
    }

    const filePath = path.join(RESULT_DIR, target)
    return fs.existsSync(filePath) ? filePath : null
  }

  private readSheetRows(filePath: string): Record<string, unknown>[] {
    const workbook = xlsx.readFile(filePath)
    const sheetName = workbook.SheetNames[0]
    if (!sheetName) {
      return []
    }
    const sheet = workbook.Sheets[sheetName]
    return xlsx.utils.sheet_to_json<Record<string, unknown>>(sheet, {
      defval: '',
    })
  }

  private resolveFirstExisting(...fileNames: string[]): string | null {
    for (const name of fileNames) {
      const filePath = path.join(RESULT_DIR, name)
      if (fs.existsSync(filePath)) {
        return filePath
      }
    }
    return null
  }

  private buildFileItem(filePath: string): ResultFileItem | null {
    if (!fs.existsSync(filePath)) {
      return null
    }

    const stats = fs.statSync(filePath)
    return {
      name: path.basename(filePath),
      path: path.relative(RESULT_DIR, filePath).replace(/\\/g, '/'),
      updatedAt: stats.mtime.toISOString(),
      size: stats.size,
    }
  }
}

function inferLatestTask(files: ResultFileItem[]): 'qs' | 'lianjia' | null {
  const latest = files[0]
  if (!latest) {
    return null
  }
  return latest.name.includes('QSRank') ? 'qs' : 'lianjia'
}

function countFiles(dirPath: string): number {
  if (!fs.existsSync(dirPath)) {
    return 0
  }
  return fs.readdirSync(dirPath).length
}

