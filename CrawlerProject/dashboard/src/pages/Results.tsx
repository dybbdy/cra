import { useEffect } from 'react'
import { FileCard } from '@/components/FileCard'
import { ResultTable } from '@/components/ResultTable'
import { useCrawlerStore } from '@/store/useCrawlerStore'

export default function Results() {
  const loadResults = useCrawlerStore((state) => state.loadResults)
  const resultFiles = useCrawlerStore((state) => state.resultFiles)
  const qsRecords = useCrawlerStore((state) => state.qsRecords)
  const lianjiaPublicRecords = useCrawlerStore((state) => state.lianjiaPublicRecords)
  const lianjiaLoginRecords = useCrawlerStore((state) => state.lianjiaLoginRecords)

  useEffect(() => {
    void loadResults()
  }, [loadResults])

  return (
    <div className="space-y-6">
      <section className="rounded-[32px] border border-white/10 bg-white/5 p-8 backdrop-blur">
        <p className="text-sm uppercase tracking-[0.3em] text-orange-200">Result Center</p>
        <h1 className="mt-4 font-serif text-4xl text-white">抓取结果查看与下载</h1>
        <p className="mt-4 max-w-3xl text-base leading-8 text-slate-300">
          统一浏览 QS 排名结果、链家公开数据与登录增强数据，并直接下载课程实验要求的产出文件。
        </p>
      </section>

      <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
        {resultFiles.map((file) => (
          <FileCard key={file.name} file={file} />
        ))}
      </section>

      <ResultTable
        title="QS 排名结果"
        description="来自 Result/QSRank.txt，展示学校名称、排名、分数、城市、国家和 Logo 地址。"
        columns={['学校名称', '排名', '分数', '城市', '国家', 'Logo URL']}
        rows={qsRecords}
      />

      <ResultTable
        title="链家公开字段"
        description="未登录即可获取的公开字段，适合核对房源基础信息和导出结果完整性。"
        columns={['小区名', '户型', '面积', '朝向', '楼层', '总价', '单价']}
        rows={lianjiaPublicRecords}
      />

      <ResultTable
        title="链家登录增强字段"
        description="登录并访问详情页后生成的增强结果，包含脱敏姓名、电话密文与 HMAC 认证码；若详情页抓取数未覆盖全部房源，后续行会保留为空。"
        columns={['小区名', '脱敏姓名', '电话密文', 'HMAC']}
        rows={lianjiaLoginRecords}
      />
    </div>
  )
}
