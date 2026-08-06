import type { SourceInfo } from "../api";

export interface Message {
  role: "user" | "assistant";
  text: string;
  source?: SourceInfo | null;
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className={`bubble-row ${isUser ? "user" : "assistant"}`}>
      <div className="avatar">{isUser ? "U" : "X"}</div>
      <div className="bubble">
        {message.text}
        {message.source && (
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
