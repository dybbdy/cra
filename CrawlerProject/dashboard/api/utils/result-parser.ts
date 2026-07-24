import type { LianjiaLoginRecord, LianjiaPublicRecord, QsRecord } from '../types.js'

export function parseQsText(content: string): QsRecord[] {
  const blocks = content
    .split('------------------------------------------------------------')
    .map((item) => item.trim())
    .filter(Boolean)

  return blocks
    .map((block) => {
      const record = {
        学校名称: '',
        排名: '',
        分数: '',
        城市: '',
        国家: '',
        'Logo URL': '',
      }

      for (const rawLine of block.split(/\r?\n/)) {
        const line = rawLine.trim()
        if (line.startsWith('学校名称：')) {
          record.学校名称 = line.replace('学校名称：', '').trim()
        } else if (line.startsWith('排名：')) {
          record.排名 = line.replace('排名：', '').trim()
        } else if (line.startsWith('分数：')) {
          record.分数 = line.replace('分数：', '').trim()
        } else if (line.startsWith('城市：')) {
          record.城市 = line.replace('城市：', '').trim()
        } else if (line.startsWith('国家：')) {
          record.国家 = line.replace('国家：', '').trim()
        } else if (line.startsWith('Logo URL：')) {
          record['Logo URL'] = line.replace('Logo URL：', '').trim()
        }
      }

      return record
    })
    .filter((item) => item.学校名称)
}

export function normalizePublicRows(rows: Record<string, unknown>[]): LianjiaPublicRecord[] {
  return rows.map((row) => ({
    小区名: normalizeCell(row.小区名),
    户型: normalizeCell(row.户型),
    面积: normalizeCell(row.面积),
    朝向: normalizeCell(row.朝向),
    楼层: normalizeCell(row.楼层),
    总价: normalizeCell(row.总价),
    单价: normalizeCell(row.单价),
  }))
}

export function normalizeLoginRows(rows: Record<string, unknown>[]): LianjiaLoginRecord[] {
  return rows.map((row) => ({
    小区名: normalizeCell(row.小区名),
    户型: normalizeCell(row.户型),
    面积: normalizeCell(row.面积),
    朝向: normalizeCell(row.朝向),
    楼层: normalizeCell(row.楼层),
    总价: normalizeCell(row.总价),
    单价: normalizeCell(row.单价),
    脱敏姓名: normalizeCell(row.脱敏姓名),
    电话密文: normalizeCell(row.电话密文),
    HMAC: normalizeCell(row.HMAC),
  }))
}

function normalizeCell(value: unknown): string {
  if (value === null || value === undefined) {
    return ''
  }
  return String(value).trim()
}

