import { describe, expect, it } from 'vitest'
import {
  normalizeLoginRows,
  normalizePublicRows,
  parseQsText,
} from './result-parser.js'

describe('result-parser', () => {
  it('应正确解析 QS 文本结果', () => {
    const records = parseQsText(`
第1条
学校名称：Massachusetts Institute of Technology (MIT)
排名：1
分数：100
城市：Cambridge
国家：United States
Logo URL：https://example.com/mit.jpg
------------------------------------------------------------
    `)

    expect(records).toHaveLength(1)
    expect(records[0]).toEqual({
      学校名称: 'Massachusetts Institute of Technology (MIT)',
      排名: '1',
      分数: '100',
      城市: 'Cambridge',
      国家: 'United States',
      'Logo URL': 'https://example.com/mit.jpg',
    })
  })

  it('应补齐链家公开结果空值', () => {
    const records = normalizePublicRows([
      { 小区名: '望京花园', 户型: '2室1厅', 面积: 88.5 },
    ])

    expect(records[0].面积).toBe('88.5')
    expect(records[0].朝向).toBe('')
    expect(records[0].楼层).toBe('')
  })

  it('应保留链家增强结果中的密文与认证码', () => {
    const records = normalizeLoginRows([
      { 小区名: '望京花园', 脱敏姓名: '张*', 电话密文: 'abc', HMAC: '123' },
    ])

    expect(records[0].脱敏姓名).toBe('张*')
    expect(records[0].电话密文).toBe('abc')
    expect(records[0].HMAC).toBe('123')
  })
})

