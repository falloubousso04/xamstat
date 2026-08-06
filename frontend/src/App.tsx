import { useEffect, useRef, useState } from "react";
import { toPng } from "html-to-image";
import { askQuestion, fetchSuggestions } from "./api";
import type { ChartSpec, Indicator, SourceInfo } from "./api";
import { MessageBubble } from "./components/MessageBubble";
import type { Message } from "./components/MessageBubble";
import { SuggestedQuestions } from "./components/SuggestedQuestions";
import { ChartPanel } from "./components/ChartPanel";
import { MapPanel } from "./components/MapPanel";

const WELCOME: Message = {
  role: "assistant",
  text:
    "Bonjour, je suis XamStat. Posez-moi une question sur la population, la pauvreté ou la densité dans les régions du Sénégal — par exemple « Quelle est la région la plus pauvre ? »",
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [chart, setChart] = useState<ChartSpec | null>(null);
  const [source, setSource] = useState<SourceInfo | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string>("");
  const [lastIndicator, setLastIndicator] = useState<Indicator | null>(null);
  const [exporting, setExporting] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const vizBodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSuggestions().then(setSuggestions).catch(() => setSuggestions([]));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || loading) return;
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setInput("");
    setLoading(true);
    try {
      const res = await askQuestion(q, lastIndicator);
      setMessages((prev) => [...prev, { role: "assistant", text: res.answer, source: res.source }]);
      setChart(res.chart.type === "none" ? null : res.chart);
      setSource(res.source);
      setLastQuestion(q);
      if (res.indicator) setLastIndicator(res.indicator);
      if (res.suggestions.length) setSuggestions(res.suggestions);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Une erreur est survenue en contactant le serveur. Réessayez dans un instant." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function exportChart() {
    if (!vizBodyRef.current || exporting) return;
    setExporting(true);
    try {
      const dataUrl = await toPng(vizBodyRef.current, { backgroundColor: "#ffffff", pixelRatio: 2 });
      const a = document.createElement("a");
      a.href = dataUrl;
      a.download = "xamstat-visualisation.png";
      a.click();
    } catch {
      // silencieux : l'export est une fonctionnalité de confort, pas critique
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>XamStat</h1>
        <span className="tagline">Interroger les statistiques du Sénégal comme une conversation</span>
      </header>
      <div className="app-body">
        <section className="chat-pane">
          <div className="messages" ref={scrollRef}>
            {messages.map((m, i) => (
              <MessageBubble key={i} message={m} />
            ))}
            {loading && <MessageBubble message={{ role: "assistant", text: "…" }} />}
          </div>
          <SuggestedQuestions suggestions={suggestions} onPick={send} disabled={loading} />
          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Posez votre question sur les données ANSD…"
              disabled={loading}
            />
            <button type="submit" disabled={loading || !input.trim()}>
              Envoyer
            </button>
          </form>
        </section>
        <section className="viz-pane">
          <div className="viz-header">
            <div className="viz-header-row">
              <div>
                <div className="kicker">Visualisation</div>
                <h2>{lastQuestion || "En attente d'une question"}</h2>
              </div>
              {chart && (
                <button className="export-btn" onClick={exportChart} disabled={exporting} title="Télécharger en PNG">
                  {exporting ? "…" : "⭳ PNG"}
                </button>
              )}
            </div>
          </div>
          <div className="viz-body" ref={vizBodyRef}>
            {!chart && (
              <div className="viz-empty">
                Le graphique ou la carte généré à partir de votre question apparaîtra ici.
              </div>
            )}
            {chart && (
              <div className="viz-fade" key={lastQuestion}>
                {chart.type === "bar" && <ChartPanel series={chart.series} unit={chart.unit} />}
                {chart.type === "map" && <MapPanel series={chart.series} unit={chart.unit} />}
              </div>
            )}
          </div>
          {source && (
            <div className="source" style={{ padding: "0 20px 16px" }}>
              Source : {source.report} — {source.table}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
