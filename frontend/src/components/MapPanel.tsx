import { useEffect, useMemo, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import type { Layer, PathOptions } from "leaflet";
import { geoJSON as LGeoJSON } from "leaflet";
import "leaflet/dist/leaflet.css";
import type { ChartSeriesPoint } from "../api";
import { fetchGeoJson } from "../api";

const COMBINING_MARKS = /[̀-ͯ]/g;

function normalizeName(s: string): string {
  return s
    .normalize("NFKD")
    .replace(COMBINING_MARKS, "")
    .replace(/-/g, " ")
    .toLowerCase()
    .trim();
}

function lerpColor(t: number): string {
  // Dégradé or clair -> bleu marine, cohérent avec la charte du dossier.
  const from = [232, 200, 119];
  const to = [11, 37, 69];
  const rgb = from.map((f, i) => Math.round(f + (to[i] - f) * t));
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

function formatValue(value: number, unit: string): string {
  if (unit === "%") return `${value.toLocaleString("fr-FR")} %`;
  return `${Math.round(value).toLocaleString("fr-FR")} ${unit}`;
}

function FitToData({ geo }: { geo: GeoJSON.FeatureCollection }) {
  const map = useMap();
  useEffect(() => {
    const bounds = LGeoJSON(geo).getBounds();
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [12, 12] });
  }, [geo, map]);
  return null;
}

export function MapPanel({ series, unit }: { series: ChartSeriesPoint[]; unit: string }) {
  const [geo, setGeo] = useState<GeoJSON.FeatureCollection | null>(null);

  useEffect(() => {
    fetchGeoJson().then(setGeo).catch(() => setGeo(null));
  }, []);

  const byName = useMemo(() => {
    const map = new Map<string, number>();
    for (const s of series) map.set(normalizeName(s.label), s.value);
    return map;
  }, [series]);

  const [min, max] = useMemo(() => {
    const values = series.map((s) => s.value);
    return [Math.min(...values), Math.max(...values)];
  }, [series]);

  if (!geo) {
    return <div className="viz-empty">Chargement de la carte…</div>;
  }

  const style = (feature?: GeoJSON.Feature): PathOptions => {
    const name = normalizeName((feature?.properties as { shapeName?: string })?.shapeName ?? "");
    const value = byName.get(name);
    const t = value === undefined || max === min ? 0.3 : (value - min) / (max - min);
    return {
      fillColor: value === undefined ? "#ddd" : lerpColor(t),
      fillOpacity: 0.85,
      color: "#fff",
      weight: 1,
    };
  };

  const onEachFeature = (feature: GeoJSON.Feature, layer: Layer) => {
    const name = (feature.properties as { shapeName?: string })?.shapeName ?? "";
    const value = byName.get(normalizeName(name));
    layer.bindTooltip(
      `<strong>${name}</strong><br/>${value !== undefined ? formatValue(value, unit) : "Donnée non disponible"}`,
    );
  };

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ flex: 1, minHeight: 0 }}>
        <MapContainer center={[14.4974, -14.4524]} zoom={6.2} scrollWheelZoom={false} attributionControl={false}>
          <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />
          <GeoJSON data={geo} style={style} onEachFeature={onEachFeature} />
          <FitToData geo={geo} />
        </MapContainer>
      </div>
      <div className="map-legend">
        <span>{formatValue(min, unit)}</span>
        <span
          className="swatch"
          style={{ background: `linear-gradient(90deg, ${lerpColor(0)}, ${lerpColor(1)})` }}
        />
        <span>{formatValue(max, unit)}</span>
      </div>
    </div>
  );
}
