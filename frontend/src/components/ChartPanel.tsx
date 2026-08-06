import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartSeriesPoint } from "../api";

const NAVY = "#0b2545";
const GOLD = "#c79a3d";

function formatValue(value: number, unit: string): string {
  if (unit === "%") return `${value.toLocaleString("fr-FR")} %`;
  return `${Math.round(value).toLocaleString("fr-FR")} ${unit}`;
}

export function ChartPanel({ series, unit }: { series: ChartSeriesPoint[]; unit: string }) {
  const data = series.map((s) => ({ name: s.label, value: s.value }));
  const isNational = (name: string) => name.toLowerCase().includes("national") || name.toLowerCase().includes("sénégal");

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e0d3" horizontal={false} />
        <XAxis type="number" tickFormatter={(v) => formatValue(v, unit)} tick={{ fontSize: 11 }} />
        <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 12.5 }} />
        <Tooltip formatter={(v) => formatValue(Number(v), unit)} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={isNational(entry.name) ? GOLD : NAVY} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
