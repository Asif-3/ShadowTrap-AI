import { GlassCard, EmptyState, SectionHeader } from '../common'

const HOURS = ['00', '03', '06', '09', '12', '15', '18', '21']
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const EMPTY_HEAT_DATA = [
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
]

export default function ThreatHeatmap({ heatData }) {
  const data = heatData || EMPTY_HEAT_DATA
  const hasData = data.some(row => row.some(v => v > 0))

  const getCellColor = (val) => {
    if (val === 0) return 'rgba(255, 255, 255, 0.03)'
    if (val < 5) return 'rgba(0, 245, 160, 0.2)'
    if (val < 15) return 'rgba(0, 245, 160, 0.5)'
    if (val < 25) return 'rgba(245, 196, 81, 0.7)'
    return 'rgba(255, 77, 103, 0.85)'
  }

  return (
    <GlassCard className="p-5 flex flex-col justify-between h-full">
      <SectionHeader title="Attack Velocity Heatmap" badge="Hourly" />

      {!hasData ? (
        <EmptyState preset="heatmap" size="sm" />
      ) : (
        <div className="overflow-x-auto my-auto py-1">
          <div className="min-w-[280px]">
            {/* Header hours */}
            <div className="grid grid-cols-9 gap-1 mb-1.5 text-center">
              <div className="text-[10px] text-[#607A71]" />
              {HOURS.map((h) => (
                <div key={h} className="text-[10px] font-mono text-[#607A71]">{h}:00</div>
              ))}
            </div>

            {/* Grid rows */}
            {DAYS.map((day, rIdx) => (
              <div key={day} className="grid grid-cols-9 gap-1 mb-1.5 items-center">
                <div className="text-[10px] font-semibold text-[#9BB7AD] font-sans">{day}</div>
                {HOURS.map((_, cIdx) => {
                  const val = data[rIdx][cIdx]
                  return (
                    <div
                      key={cIdx}
                      title={`${day} ${HOURS[cIdx]}:00 — ${val} attacks`}
                      className="h-5 rounded transition-all hover:scale-105 cursor-pointer flex items-center justify-center text-[9px] font-mono font-bold text-[#E8FFF6]"
                      style={{ background: getCellColor(val) }}
                    >
                      {val > 10 ? val : ''}
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="w-full pt-3 border-t border-[rgba(0,245,160,0.1)] flex justify-between text-[11px] font-mono text-[#9BB7AD]">
        <span>CADENCE</span>
        <span className="text-[#00F5A0] font-semibold">WEEKLY AGGREGATE</span>
      </div>
    </GlassCard>
  )
}
