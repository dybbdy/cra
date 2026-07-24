interface ResultTableProps<T extends object> {
  title: string
  description: string
  columns: Array<Extract<keyof T, string>>
  rows: T[]
}

export function ResultTable<T extends object>({
  title,
  description,
  columns,
  rows,
}: ResultTableProps<T>) {
  return (
    <section className="rounded-[28px] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div className="mb-5">
        <h3 className="font-serif text-2xl text-white">{title}</h3>
        <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
      </div>

      <div className="overflow-auto rounded-3xl border border-white/10">
        <table className="min-w-full divide-y divide-white/10 text-left text-sm">
          <thead className="bg-slate-950/60 text-slate-300">
            <tr>
              {columns.map((column) => (
                <th key={String(column)} className="whitespace-nowrap px-4 py-3 font-medium">
                  {String(column)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 bg-slate-950/20 text-slate-100">
            {rows.length === 0 ? (
              <tr>
                <td className="px-4 py-12 text-center text-slate-500" colSpan={columns.length}>
                  暂无结果，请先执行抓取任务。
                </td>
              </tr>
            ) : (
              rows.map((row, index) => (
                <tr key={`${title}-${index}`} className="hover:bg-white/[0.03]">
                  {columns.map((column) => (
                    <td key={String(column)} className="max-w-[280px] px-4 py-3 align-top text-slate-300">
                      <div className="truncate" title={String(row[column] ?? '')}>
                        {String(row[column] ?? '—')}
                      </div>
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
