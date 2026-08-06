export interface ChartSeriesPoint {
  label: string;
  value: number;
}

export interface ChartSpec {
  type: "bar" | "map" | "none";
  unit: string;
  series: ChartSeriesPoint[];
  indicator: "poverty_rate" | "population" | null;
}

export interface SourceInfo {
  report: string;
  table: string;
  url: string;
}

export interface AskResponse {
  answer: string;
  chart: ChartSpec;
  source: SourceInfo | null;
  suggestions: string[];
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    throw new Error(`Erreur API (${res.status})`);
  }
  return res.json();
}

export async function fetchSuggestions(): Promise<string[]> {
  const res = await fetch("/api/suggestions");
  const data = await res.json();
  return data.suggestions;
}

export async function fetchGeoJson(): Promise<GeoJSON.FeatureCollection> {
  const res = await fetch("/api/geojson");
  return res.json();
}
