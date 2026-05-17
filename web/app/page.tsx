"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Trash2 } from "lucide-react";
import { ChatMessages } from "@/components/chat/ChatMessages";
import { ChatInput } from "@/components/chat/ChatInput";
import { DebugPanel } from "@/components/debug/DebugPanel";
import { streamChat, fetchInfo } from "@/lib/api";
import type { AgentEvent, ApiInfo, ChatMessage } from "@/lib/types";

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [debugMode, setDebugMode] = useState(false);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [stepIndex, setStepIndex] = useState(0);
  const [info, setInfo] = useState<ApiInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Busca info da API no boot pra mostrar provider/tools no header
  useEffect(() => {
    fetchInfo()
      .then(setInfo)
      .catch((e: Error) =>
        setError(`Backend indisponível: ${e.message}. Rode \`uvicorn insurmind.api:app --port 8000\` no diretório do projeto.`),
      );
  }, []);

  const allRevealed = events.length === 0 || stepIndex >= events.length - 1;

  const sendMessage = useCallback(
    async (text: string) => {
      setError(null);
      const userMsg: ChatMessage = { role: "user", content: text };
      const history = [...messages, userMsg];
      setMessages(history);
      setIsLoading(true);
      setEvents([]);
      setStepIndex(0);

      const collected: AgentEvent[] = [];
      let finalText = "";

      try {
        await streamChat(history, (ev) => {
          collected.push(ev);
          if (ev.type === "final_answer") {
            finalText = String(ev.payload?.text ?? "");
          }
          if (ev.type === "error") {
            const msg = String(ev.payload?.message ?? "erro desconhecido");
            setError(msg);
          }
        });

        if (!finalText && collected.length === 0) {
          throw new Error("Stream vazio — agente não respondeu.");
        }
        if (!finalText) {
          // Fallback: concatena todos os llm_text recebidos
          finalText = collected
            .filter((e) => e.type === "llm_text")
            .map((e) => String(e.payload?.text ?? ""))
            .join("");
        }

        setMessages((prev) => [...prev, { role: "assistant", content: finalText }]);
        setEvents(collected);
        // Debug ON: começa do passo 0; debug OFF: revela tudo imediatamente
        setStepIndex(debugMode ? 0 : Math.max(0, collected.length - 1));
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    [messages, debugMode],
  );

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="border-b border-zinc-200 bg-white px-6 py-3 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🚗</span>
            <div>
              <h1 className="text-lg font-semibold text-zinc-900">
                InsurMind <span className="text-zinc-400">—</span>{" "}
                <span className="text-blue-700">Porto Inseguro</span>
              </h1>
              <p className="text-xs text-zinc-500">
                Chatbot acadêmico de seguro auto · curso I2A2 InsurMinds · seguradora{" "}
                <strong>fictícia</strong>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {info && (
              <Badge variant="outline" className="font-mono text-xs">
                {info.provider} · {info.tools.length} tools
              </Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setMessages([]);
                setEvents([]);
                setStepIndex(0);
                setError(null);
              }}
              className="gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Limpar conversa
            </Button>
            <label className="flex cursor-pointer items-center gap-2 rounded-md border border-zinc-200 px-3 py-1.5 hover:bg-zinc-50">
              <span className="text-lg">🪲</span>
              <span className="text-sm font-medium text-zinc-700">Modo Debug</span>
              <Switch checked={debugMode} onCheckedChange={setDebugMode} />
            </label>
          </div>
        </div>
      </header>

      {error && (
        <div className="border-b border-red-200 bg-red-50 px-6 py-2 text-sm text-red-800">
          ❌ {error}
        </div>
      )}

      {/* Conteúdo principal */}
      <main className="flex flex-1 overflow-hidden">
        {/* Chat */}
        <section
          className={`flex flex-col bg-white ${
            debugMode ? "w-3/5 border-r border-zinc-200" : "flex-1"
          }`}
        >
          <ChatMessages
            messages={messages}
            isLoading={isLoading}
            debugMode={debugMode}
            shouldHideLastAnswer={!allRevealed}
          />
          <ChatInput onSend={sendMessage} disabled={isLoading} />
        </section>

        {/* Painel Debug (lateral) */}
        {debugMode && (
          <aside className="w-2/5">
            <DebugPanel
              events={events}
              stepIndex={stepIndex}
              onNext={() =>
                setStepIndex((i) => Math.min(events.length - 1, i + 1))
              }
              onSkipToEnd={() => setStepIndex(Math.max(0, events.length - 1))}
            />
          </aside>
        )}
      </main>

      {/* Rodapé */}
      <footer className="border-t border-zinc-200 bg-zinc-100 px-6 py-2 text-center text-xs text-zinc-500">
        ⚠️ Valores e regras são simulados para fins acadêmicos (curso I2A2
        InsurMinds, Atividade Obrigatória 2). <strong>Porto Inseguro</strong> é
        uma seguradora <strong>fictícia</strong> — o conteúdo da base de
        conhecimento foi anonimizado a partir de materiais públicos de uma
        seguradora real.
      </footer>
    </div>
  );
}
