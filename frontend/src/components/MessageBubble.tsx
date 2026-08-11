import { useEffect, useState } from "react";
import type { ChartSpec, SourceInfo } from "../api";

export interface Message {
  role: "user" | "assistant";
  text: string;
  source?: SourceInfo | null;
  chart?: ChartSpec | null;
  question?: string;
}

/** Révèle le texte progressivement (une seule fois, au premier montage du composant). */
function useTypewriter(text: string, enabled: boolean): string {
  const [length, setLength] = useState(enabled ? 0 : text.length);

  useEffect(() => {
    if (!enabled) return;
    const charsPerTick = Math.max(1, Math.ceil(text.length / 60));
    const id = setInterval(() => {
      setLength((prev) => {
        const next = prev + charsPerTick;
        if (next >= text.length) clearInterval(id);
        return Math.min(next, text.length);
      });
    }, 16);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return text.slice(0, length);
}

export function MessageBubble({
  message,
  onShowChart,
}: {
  message: Message;
  onShowChart?: (message: Message) => void;
}) {
  const isUser = message.role === "user";
  const displayText = useTypewriter(message.text, !isUser);
  const fullyRevealed = displayText.length === message.text.length;
  const hasChart = message.chart && message.chart.type !== "none";

  return (
    <div className={`bubble-row ${isUser ? "user" : "assistant"}`}>
      <div className="avatar">{isUser ? "U" : "X"}</div>
      <div className="bubble">
        {displayText}
        {message.source && fullyRevealed && (
          <div className="source">
            Source : {message.source.report}
            {" — "}
            <a href={message.source.url} target="_blank" rel="noreferrer">
              {message.source.table}
            </a>
          </div>
        )}
        {hasChart && fullyRevealed && onShowChart && (
          <button className="chart-toggle-btn" onClick={() => onShowChart(message)}>
            Voir le graphique
          </button>
        )}
      </div>
    </div>
  );
}
