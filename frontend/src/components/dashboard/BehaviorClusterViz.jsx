import { GlassCard, EmptyState, SectionHeader } from '../common'
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, Tooltip, Cell } from 'recharts'

export default function BehaviorClusterViz({ clusters = [] }) {
  return (
    <GlassCard className="p-5 flex flex-col justify-between h-full">
      <SectionHeader title="Behavior Clustering (DBSCAN)" badge="AI Engine" />

      {clusters.length === 0 ? (
        <EmptyState preset="cluster" size="sm" />
      ) : (
        <>
          <ResponsiveContainer width="100%" height={180}>
            <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: -20 }}>
              <XAxis type="number" dataKey="x" name="Complexity" tick={{ fill: '#607A71', fontSize: 10 }} axisLine={false} />
              <YAxis type="number" dataKey="y" name="Threat Index" tick={{ fill: '#607A71', fontSize: 10 }} axisLine={false} />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{
                  background: '#0B1412',
                  border: '1px solid rgba(0, 245, 160, 0.2)',
                  borderRadius: 8,
                  fontSize: 11,
                  color: '#E8FFF6',
                  fontFamily: 'Inter',
                }}
              />
              <Scatter data={clusters} fill="#00F5A0">
                {clusters.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color || '#00F5A0'} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>

          <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t border-[rgba(0,245,160,0.1)]">
            {clusters.map((c) => (
              <div key={c.cluster} className="flex items-center gap-1.5 text-[10px] font-medium font-sans">
                <span className="w-2 h-2 rounded-full inline-block" style={{ background: c.color || '#00F5A0' }} />
                <span className="text-[#9BB7AD]">{c.label}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </GlassCard>
  )
}
