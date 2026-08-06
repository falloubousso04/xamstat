import { useEffect, useState } from "react";
import type { SourceInfo } from "../api";

export interface Message {
  role: "user" | "assistant";
  text: string;
  source?: SourceInfo | null;
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

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const displayText = useTypewriter(message.text, !isUser);

  return (
    <div className={`bubble-row ${isUser ? "user" : "assistant"}`}>
      <div className="avatar">{isUser ? "U" : "X"}</div>
      <div className="bubble">
        {displayText}
        {message.source && displayText.length === message.text.length && (
          <div className="source">
            Source : {message.source.report}
            {" — "}
            <a href={message.source.url} target="_blank" rel="noreferrer">
              {message.source.table}
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
