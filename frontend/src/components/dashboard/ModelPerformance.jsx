import { GlassCard, EmptyState, SectionHeader } from '../common'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'
import { CheckCircle2 } from 'lucide-react'

export default function ModelPerformance({ performanceData = [], currentMetrics = null }) {
  const hasData = performanceData.length > 0

  return (
    <GlassCard className="p-5 flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-3">
        <SectionHeader title="Model Performance & Retraining" className="mb-0" />
        {hasData && (
          <span className="flex items-center gap-1 text-[10px] font-mono font-semibold text-[#20E67A] bg-[rgba(32,230,122,0.1)] px-2 py-0.5 rounded border border-[rgba(32,230,122,0.25)]">
            <CheckCircle2 size={11} /> Ensemble Active
          </span>
        )}
      </div>

      {!hasData ? (
        <EmptyState preset="model" size="sm" />
      ) : (
        <>
          {/* Metric Summary Badges */}
          <div className="grid grid-cols-3 gap-2.5 mb-3">
            <div className="p-2.5 rounded-lg bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
              <p className="text-[10px] text-[#607A71] font-mono">Accuracy</p>
              <p className="text-base font-bold font-mono text-[#00F5A0]">
                {currentMetrics?.accuracy ?? performanceData[performanceData.length - 1]?.accuracy ?? '—'}%
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
              <p className="text-[10px] text-[#607A71] font-mono">F1 Score</p>
              <p className="text-base font-bold font-mono text-[#4DB8FF]">
                {currentMetrics?.f1 ?? '—'}
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-[#08110F] border border-[rgba(0,245,160,0.12)]">
              <p className="text-[10px] text-[#607A71] font-mono">Inference</p>
              <p className="text-base font-bold font-mono text-[#20E67A]">
                {currentMetrics?.inference ?? '—'}
              </p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={performanceData}>
              <XAxis dataKey="epoch" tick={{ fill: '#607A71', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis domain={[80, 100]} tick={{ fill: '#607A71', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  background: '#0B1412',
                  border: '1px solid rgba(0, 245, 160, 0.2)',
                  borderRadius: 8,
                  fontSize: 11,
                  color: '#E8FFF6',
                  fontFamily: 'Inter',
                }}
              />
              <Line type="monotone" dataKey="accuracy" stroke="#00F5A0" strokeWidth={2} dot={{ r: 3, fill: '#00F5A0' }} />
            </LineChart>
          </ResponsiveContainer>
        </>
      )}
    </GlassCard>
  )
}
