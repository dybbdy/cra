import { Download, FileText } from 'lucide-react'
import type { ResultFileItem } from '@/types/dashboard'
import { formatDateTime, formatFileSize } from '@/utils/api'

export function FileCard({ file }: { file: ResultFileItem }) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-white/5 p-5 backdrop-blur">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-3 text-cyan-200">
            <FileText className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm text-slate-400">结果文件</p>
            <p className="mt-1 text-base text-white">{file.name}</p>
          </div>
        </div>
        <a
          href={`/api/files/download?name=${encodeURIComponent(file.name)}`}
          className="inline-flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-sm text-slate-200 transition hover:bg-white/5"
        >
          <Download className="h-4 w-4" />
          下载
        </a>
      </div>

      <div className="space-y-2 text-sm text-slate-400">
        <p>更新时间：{formatDateTime(file.updatedAt)}</p>
        <p>文件大小：{formatFileSize(file.size)}</p>
        <p>相对路径：Result/{file.path}</p>
      </div>
    </div>
  )
}

