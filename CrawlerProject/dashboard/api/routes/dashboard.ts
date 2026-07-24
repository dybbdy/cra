import fs from 'node:fs'
import { Router } from 'express'
import { ResultService } from '../services/result-service.js'
import { taskManager } from '../services/task-manager.js'
import type { RunTaskRequest } from '../types.js'

const router = Router()
const resultService = new ResultService()

router.get('/overview', (_req, res) => {
  const overview = resultService.getOverview()
  res.json({
    ...overview,
    running: taskManager.getStatus().running,
    taskStatus: taskManager.getStatus(),
  })
})

router.post('/tasks/run', async (req, res) => {
  try {
    const payload = req.body as RunTaskRequest
    if (!payload?.crawler) {
      res.status(400).json({ message: '缺少 crawler 参数。' })
      return
    }

    const status = await taskManager.runTask(payload)
    res.json({ success: true, status })
  } catch (error) {
    res.status(400).json({
      success: false,
      message: error instanceof Error ? error.message : '任务启动失败',
    })
  }
})

router.post('/tasks/stop', async (_req, res) => {
  const stopped = await taskManager.stopTask()
  res.json({ success: stopped })
})

router.get('/tasks/status', (_req, res) => {
  res.json(taskManager.getStatus())
})

router.get('/tasks/log-stream', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    Connection: 'keep-alive',
  })
  res.write('\n')

  taskManager.subscribe(res)
  req.on('close', () => {
    taskManager.unsubscribe(res)
  })
})

router.get('/results/qs', (_req, res) => {
  res.json(resultService.getQsRecords())
})

router.get('/results/lianjia/public', (_req, res) => {
  res.json(resultService.getLianjiaPublicRecords())
})

router.get('/results/lianjia/login', (_req, res) => {
  res.json(resultService.getLianjiaLoginRecords())
})

router.get('/files', (_req, res) => {
  res.json(resultService.listResultFiles())
})

router.get('/files/download', (req, res) => {
  const fileName = String(req.query.name || '')
  const target = resultService.getDownloadPath(fileName)
  if (!target || !fs.existsSync(target)) {
    res.status(404).json({ message: '文件不存在。' })
    return
  }
  res.download(target, fileName)
})

router.post('/files/open-directory', (_req, res) => {
  taskManager.openResultDirectory()
  res.json({ success: true })
})

export default router

