import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { EmptyState } from '../common'

const DEFAULT_MAP_CENTER = [20.0, 0.0]

export default function WorldAttackMap({ locations = [] }) {
  const getMarkerColor = (score) => {
    if (score >= 80) return '#FF4D67'
    if (score >= 60) return '#FF7043'
    if (score >= 35) return '#F5C451'
    return '#20E67A'
  }

  return (
    <div className="w-full h-[280px] rounded-lg overflow-hidden relative border border-[rgba(0,245,160,0.14)]">
      <MapContainer
        center={DEFAULT_MAP_CENTER}
        zoom={2}
        scrollWheelZoom={false}
        className="w-full h-full z-0"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap'
        />
        {locations.map((loc, idx) => (
          <CircleMarker
            key={idx}
            center={[loc.lat, loc.lng]}
            radius={Math.min(16, Math.max(5, loc.count / 4))}
            pathOptions={{
              color: getMarkerColor(loc.score),
              fillColor: getMarkerColor(loc.score),
              fillOpacity: 0.65,
              weight: 1.5,
            }}
          >
            <Popup>
              <div className="p-1 text-xs space-y-1 font-sans">
                <p className="font-bold text-[#050908]">{loc.city}, {loc.country}</p>
                <p className="font-mono text-[#008855]">IP: {loc.ip}</p>
                <p className="text-[#333]">Attacks: <strong>{loc.count}</strong></p>
                <p className="font-bold" style={{ color: getMarkerColor(loc.score) }}>Threat Score: {loc.score}/100</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Empty state overlay */}
      {locations.length === 0 && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#050908]/80 backdrop-blur-xs">
          <EmptyState preset="map" size="sm" />
        </div>
      )}

      {/* Legend overlay */}
      {locations.length > 0 && (
        <div className="absolute bottom-2.5 left-2.5 bg-[#0B1412]/90 border border-[rgba(0,245,160,0.2)] px-2.5 py-1.5 rounded-md z-10 text-[10px] flex items-center gap-3 font-mono">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#FF4D67] inline-block" /> Critical</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#FF7043] inline-block" /> High</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#20E67A] inline-block" /> Low</span>
        </div>
      )}
    </div>
  )
}
