import React, { useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, Marker, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';

// Tamil Nadu center and zoom
const TN_CENTER = [10.8, 78.7];
const TN_ZOOM = 7;

function getRiskColor(score) {
  if (score >= 0.65) return '#ef4444';
  if (score >= 0.3) return '#f59e0b';
  return '#00d4ff';
}

function getRiskLevel(score) {
  if (score >= 0.65) return 'critical';
  if (score >= 0.3) return 'moderate';
  return 'safe';
}

// Component to fly to a district when selected
function FlyToDistrict({ district, riskData }) {
  const map = useMap();
  React.useEffect(() => {
    if (district && riskData) {
      const feature = riskData.features?.find(
        (f) => f.properties.district === district
      );
      if (feature) {
        const [lon, lat] = feature.geometry.coordinates;
        map.flyTo([lat, lon], 10, { duration: 1.5 });
      }
    }
  }, [district, riskData, map]);
  return null;
}

export default function RiskMap({
  riskData,
  geoJsonData,
  selectedDistrict,
  onSelectDistrict,
  showEvacuation,
  onToggleEvacuation,
  showCrowdReports,
  onToggleCrowdReports,
  evacuationData,
  crowdReports,
  timeWindow,
}) {
  // Style GeoJSON district polygons
  const districtStyle = (feature) => {
    const districtName = feature.properties.DISTRICT || feature.properties.district || feature.properties.NAME;
    const riskFeature = riskData?.features?.find(
      (f) => f.properties.district?.toLowerCase() === districtName?.toLowerCase()
    );
    const risk = riskFeature?.properties?.risk_score || 0;
    const color = getRiskColor(risk);
    const isSelected = selectedDistrict?.toLowerCase() === districtName?.toLowerCase();

    return {
      fillColor: color,
      fillOpacity: isSelected ? 0.4 : 0.15,
      color: isSelected ? '#ffffff' : color,
      weight: isSelected ? 2.5 : 1,
      opacity: isSelected ? 1 : 0.6,
    };
  };

  const onEachDistrict = (feature, layer) => {
    const name = feature.properties.DISTRICT || feature.properties.district || feature.properties.NAME || 'Unknown';
    const riskFeature = riskData?.features?.find(
      (f) => f.properties.district?.toLowerCase() === name?.toLowerCase()
    );
    const risk = riskFeature?.properties?.risk_score || 0;
    const pct = Math.round(risk * 100);
    const level = getRiskLevel(risk);

    layer.on('click', () => onSelectDistrict(name));
    layer.bindPopup(`
      <div class="risk-popup">
        <h4>${name}</h4>
        <div class="risk-value" style="color:${getRiskColor(risk)}">${pct}%</div>
        <div class="risk-details">
          Flood risk (${timeWindow || '72h'} window)<br/>
          Level: <strong style="color:${getRiskColor(risk)}">${level.toUpperCase()}</strong>
        </div>
      </div>
    `);
  };

  // Shelter icon
  const shelterIcon = useMemo(() => L.divIcon({
    html: '<div style="font-size:20px;text-align:center">🏥</div>',
    className: '',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  }), []);

  return (
    <div className="map-container">
      <MapContainer
        center={TN_CENTER}
        zoom={TN_ZOOM}
        style={{ width: '100%', height: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />

        {/* District boundaries */}
        {geoJsonData && (
          <GeoJSON
            data={geoJsonData}
            style={districtStyle}
            onEachFeature={onEachDistrict}
            key={`${selectedDistrict}-${timeWindow}`}
          />
        )}

        {/* Risk heatmap points with pulse */}
        {riskData?.features?.map((f, i) => {
          const [lon, lat] = f.geometry.coordinates;
          const risk = f.properties.risk_score;
          if (risk < 0.3) return null;
          return (
            <CircleMarker
              key={`risk-${i}`}
              center={[lat, lon]}
              radius={risk >= 0.65 ? 14 : 8}
              pathOptions={{
                fillColor: getRiskColor(risk),
                fillOpacity: 0.6,
                color: getRiskColor(risk),
                weight: 2,
                opacity: 0.8,
              }}
            >
              <Popup>
                <div className="risk-popup">
                  <h4>{f.properties.district}</h4>
                  <div className="risk-value" style={{ color: getRiskColor(risk) }}>
                    {Math.round(risk * 100)}%
                  </div>
                  <div className="risk-details">
                    {f.properties.label}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Evacuation shelters */}
        {showEvacuation && evacuationData?.shelters?.map((s, i) => (
          <Marker key={`shelter-${i}`} position={[s.lat, s.lon]} icon={shelterIcon}>
            <Popup>
              <div className="evac-popup">
                <div className="shelter-name">{s.name}</div>
                <div className="capacity">Capacity: {s.capacity} people</div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Evacuation routes */}
        {showEvacuation && evacuationData?.routes?.map((r, i) => (
          <Polyline
            key={`route-${i}`}
            positions={[
              [evacuationData.shelters?.[0]?.lat || TN_CENTER[0], evacuationData.shelters?.[0]?.lon || TN_CENTER[1]],
              [(evacuationData.shelters?.[0]?.lat || TN_CENTER[0]) + 0.02, (evacuationData.shelters?.[0]?.lon || TN_CENTER[1]) + 0.03],
            ]}
            pathOptions={{ color: '#00ff88', weight: 3, dashArray: '10, 10' }}
          />
        ))}

        {/* Crowd reports */}
        {showCrowdReports && crowdReports?.map((r, i) => (
          <CircleMarker
            key={`crowd-${i}`}
            center={[r.latitude, r.longitude]}
            radius={6}
            pathOptions={{ fillColor: '#a855f7', fillOpacity: 0.8, color: '#a855f7', weight: 1 }}
          >
            <Popup>
              <div style={{ fontSize: '12px' }}>
                <strong>{r.disaster_type}</strong> — Severity: {r.severity}/5<br />
                {r.description}<br />
                <em style={{ color: '#94a3b8' }}>{r.reporter_name} · {new Date(r.timestamp).toLocaleString()}</em>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        <FlyToDistrict district={selectedDistrict} riskData={riskData} />
      </MapContainer>

      {/* Map overlay controls */}
      <div className="map-overlay-controls">
        <button
          className={`map-overlay-btn ${showEvacuation ? 'active' : ''}`}
          onClick={onToggleEvacuation}
        >
          🚨 Evacuation Routes
        </button>
        <button
          className={`map-overlay-btn ${showCrowdReports ? 'active' : ''}`}
          onClick={onToggleCrowdReports}
        >
          📍 Crowd Reports
        </button>
      </div>
    </div>
  );
}
