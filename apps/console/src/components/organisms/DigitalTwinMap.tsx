import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { RiskFinding } from '@/types';
import { Card, Badge, Button } from '@/components/atoms';
import { Shield, Radio, Compass, Layers } from 'lucide-react';

interface DigitalTwinMapProps {
  findings: RiskFinding[];
}

const PLANT_CENTER: [number, number] = [83.2185, 17.6896];

const MOCK_ZONES_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { zoneId: 'Zone 4', name: 'Primary Reformer', baseColor: '#1c23d2', alertState: 'imminent' },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [83.217, 17.691],
            [83.220, 17.691],
            [83.220, 17.689],
            [83.217, 17.689],
            [83.217, 17.691],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { zoneId: 'Zone 12', name: 'Confined Compressor', baseColor: '#e8a33d', alertState: 'near' },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [83.214, 17.687],
            [83.217, 17.687],
            [83.217, 17.685],
            [83.214, 17.685],
            [83.214, 17.687],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { zoneId: 'Zone 2', name: 'Storage Dikes', baseColor: '#4fa3c7', alertState: 'watch' },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [83.221, 17.687],
            [83.224, 17.687],
            [83.224, 17.684],
            [83.221, 17.684],
            [83.221, 17.687],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { zoneId: 'Zone 8', name: 'Sulfur Recovery', baseColor: '#f06363', alertState: 'imminent' },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [83.218, 17.694],
            [83.221, 17.694],
            [83.221, 17.692],
            [83.218, 17.692],
            [83.218, 17.694],
          ],
        ],
      },
    },
  ],
};

const MOCK_SENSORS = [
  { id: 'CH4-0411', name: 'Methane Ingress', coordinates: [83.218, 17.690], status: 'live', value: '1.2% LEL' },
  { id: 'TEMP-1201', name: 'Bearing Thermal', coordinates: [83.215, 17.686], status: 'skewed', value: '89°C' },
  { id: 'PRES-0211', name: 'Storage Purge', coordinates: [83.222, 17.685], status: 'live', value: '1.1 bar' },
  { id: 'H2S-0814', name: 'Sulfur Detector', coordinates: [83.219, 17.693], status: 'oor', value: '15 ppm' },
];

export function DigitalTwinMap({ findings }: DigitalTwinMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [activeLayers, setActiveLayers] = useState<string[]>(['zones', 'sensors', 'findings']);
  const [selectedSensor, setSelectedSensor] = useState<typeof MOCK_SENSORS[0] | null>(null);

  const toggleLayer = (layerId: string) => {
    setActiveLayers((prev) =>
      prev.includes(layerId) ? prev.filter((id) => id !== layerId) : [...prev, layerId]
    );
  };

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Strict local stylesheet configuration to work 100% offline in air-gapped environments
    const localStyle: maplibregl.StyleSpecification = {
      version: 8,
      sources: {},
      layers: [
        {
          id: 'background',
          type: 'background',
          paint: {
            'background-color': '#0e1116',
          },
        },
      ],
    };

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: localStyle,
      center: PLANT_CENTER,
      zoom: 14.5,
      pitch: 30,
      bearing: -10,
    });

    mapRef.current = map;

    map.on('load', () => {
      // Add zones GeoJSON layer source
      map.addSource('plant-zones', {
        type: 'geojson',
        data: MOCK_ZONES_GEOJSON as any,
      });

      // Render zones fill
      map.addLayer({
        id: 'zones-fill',
        type: 'fill',
        source: 'plant-zones',
        paint: {
          'fill-color': [
            'match',
            ['get', 'alertState'],
            'imminent', 'rgba(240, 99, 99, 0.15)',
            'near', 'rgba(232, 163, 61, 0.15)',
            'watch', 'rgba(79, 163, 199, 0.15)',
            'rgba(42, 50, 61, 0.25)',
          ],
          'fill-outline-color': '#2a323d',
        },
      });

      // Render zones boundary lines
      map.addLayer({
        id: 'zones-line',
        type: 'line',
        source: 'plant-zones',
        paint: {
          'line-color': [
            'match',
            ['get', 'alertState'],
            'imminent', '#f06363',
            'near', '#e8a33d',
            'watch', '#4fa3c7',
            '#2a323d',
          ],
          'line-width': 1.5,
        },
      });
    });

    return () => {
      map.remove();
    };
  }, []);

  // Update map layer visibilities when activeLayers toggle changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('zones-fill')) {
      map.setLayoutProperty('zones-fill', 'visibility', activeLayers.includes('zones') ? 'visible' : 'none');
    }
    if (map.getLayer('zones-line')) {
      map.setLayoutProperty('zones-line', 'visibility', activeLayers.includes('zones') ? 'visible' : 'none');
    }
  }, [activeLayers]);

  return (
    <div className="h-full w-full relative flex select-none text-ink font-sans">
      {/* Map Container viewport */}
      <div ref={mapContainerRef} className="flex-1 h-full w-full bg-bg relative overflow-hidden" />

      {/* Floating Layer Controls Panel */}
      <div className="absolute top-3 left-3 flex flex-col gap-2 z-10">
        <Card className="p-2.5 bg-panel/90 border-line shadow-none flex flex-col gap-2 w-48">
          <span className="text-micro font-mono font-bold text-ink-dim uppercase tracking-wider flex items-center gap-1.5 border-b border-line pb-1.5">
            <Layers className="h-3.5 w-3.5" />
            Layer Controls
          </span>
          <div className="flex flex-col gap-1.5">
            {[
              { id: 'zones', label: 'Plant Zones', icon: <Compass className="h-3.5 w-3.5" /> },
              { id: 'sensors', label: 'IoT Sensors', icon: <Radio className="h-3.5 w-3.5" /> },
              { id: 'findings', label: 'Active Risks', icon: <Shield className="h-3.5 w-3.5" /> },
            ].map((layer) => (
              <button
                key={layer.id}
                onClick={() => toggleLayer(layer.id)}
                className={`flex items-center gap-2 h-7 px-2 rounded border text-xs font-semibold font-mono text-left cursor-pointer transition-colors ${
                  activeLayers.includes(layer.id)
                    ? 'bg-panel-2 border-accent text-accent'
                    : 'bg-transparent border-transparent text-ink-dim hover:text-ink'
                }`}
              >
                {layer.icon}
                {layer.label}
              </button>
            ))}
          </div>
        </Card>
      </div>

      {/* Floating Sensor Readings Drawer */}
      {selectedSensor && (
        <div className="absolute bottom-3 right-3 z-10 w-72">
          <Card className="p-3 bg-panel/95 border-line shadow-none flex flex-col gap-2 text-xs select-text">
            <div className="flex justify-between items-start border-b border-line pb-2">
              <div className="flex flex-col gap-0.5">
                <span className="font-bold font-mono text-ink text-sm">{selectedSensor.id}</span>
                <span className="text-micro font-mono text-ink-dim uppercase">{selectedSensor.name}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-5 px-1 hover:bg-panel-2 text-ink-dim"
                onClick={() => setSelectedSensor(null)}
              >
                Dismiss
              </Button>
            </div>
            <div className="flex justify-between items-center bg-panel-2 p-2 rounded border border-line">
              <span className="font-mono text-ink-dim">CURRENT VALUE:</span>
              <span className="font-mono font-bold text-accent text-sm tabular-nums">{selectedSensor.value}</span>
            </div>
            <div className="flex justify-between text-micro font-mono text-ink-dim">
              <span>STATUS:</span>
              <span className={`uppercase font-bold ${selectedSensor.status === 'live' ? 'text-ok' : 'text-imminent'}`}>
                {selectedSensor.status}
              </span>
            </div>
          </Card>
        </div>
      )}

      {/* Render HTML elements as overlays for markers to optimize air-gapped styling */}
      {activeLayers.includes('sensors') && (
        <div className="absolute inset-0 pointer-events-none z-10">
          {MOCK_SENSORS.map((sensor) => {
            // Simplified layout coordinate translation or absolute overlay positioning mapping
            // To ensure 100% stable offline testing, we position sensor markers over the center zones overlay
            let top = '50%';
            let left = '50%';
            if (sensor.id.includes('CH4')) { top = '38%'; left = '48%'; }
            if (sensor.id.includes('TEMP')) { top = '58%'; left = '38%'; }
            if (sensor.id.includes('PRES')) { top = '62%'; left = '64%'; }
            if (sensor.id.includes('H2S')) { top = '25%'; left = '56%'; }

            return (
              <button
                key={sensor.id}
                onClick={() => setSelectedSensor(sensor)}
                className="absolute pointer-events-auto h-3 w-3 rounded-full border border-bg bg-ok hover:scale-125 transition-transform cursor-pointer -translate-x-1/2 -translate-y-1/2 flex items-center justify-center"
                style={{
                  top,
                  left,
                  backgroundColor: sensor.status === 'live' ? '#4ec98a' : sensor.status === 'oor' ? '#f06363' : '#e8a33d',
                }}
                title={`${sensor.id}: ${sensor.value}`}
              >
                <span className="h-1 w-1 rounded-full bg-bg" />
              </button>
            );
          })}
        </div>
      )}

      {/* Render Risk Finding overlay indicators */}
      {activeLayers.includes('findings') && (
        <div className="absolute inset-0 pointer-events-none z-10">
          {findings.map((finding) => {
            let top = '32%';
            let left = '42%';
            if (finding.zoneId.includes('Zone 12')) { top = '52%'; left = '32%'; }
            if (finding.zoneId.includes('Zone 2')) { top = '58%'; left = '58%'; }
            if (finding.zoneId.includes('Zone 8')) { top = '22%'; left = '50%'; }

            return (
              <div
                key={finding.findingId}
                className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-1"
                style={{ top, left }}
              >
                {/* Pulsing hazard marker */}
                <div
                  className={`h-6 w-6 rounded-full flex items-center justify-center animate-ping absolute opacity-30`}
                  style={{
                    backgroundColor: finding.leadTimeBand === 'IMMINENT' ? '#f06363' : '#e8a33d',
                  }}
                />
                <div
                  className="h-4 w-4 rounded-full border border-bg flex items-center justify-center relative shadow-sm"
                  style={{
                    backgroundColor: finding.leadTimeBand === 'IMMINENT' ? '#f06363' : '#e8a33d',
                  }}
                >
                  <Shield className="h-2.5 w-2.5 text-bg" />
                </div>
                <Badge variant="band" band={finding.leadTimeBand} className="text-micro font-bold py-0 scale-90">
                  {finding.findingId}
                </Badge>
              </div>
            );
          })}
        </div>
      )}

      {/* Screen Reader accessible active findings table fallback */}
      <div className="sr-only">
        <table>
          <caption>Active Plant Digital Twin Hazard Locations</caption>
          <thead>
            <tr>
              <th>Finding ID</th>
              <th>Location / Zone</th>
              <th>Risk Severity</th>
              <th>Model Confidence</th>
            </tr>
          </thead>
          <tbody>
            {findings.map((f) => (
              <tr key={f.findingId}>
                <td>{f.findingId}</td>
                <td>{f.zoneId}</td>
                <td>{f.leadTimeBand}</td>
                <td>{(f.confidence * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
