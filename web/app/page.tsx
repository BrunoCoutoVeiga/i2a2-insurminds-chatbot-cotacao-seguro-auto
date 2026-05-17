"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
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
  // Default ON — o Modo Debug é a feature didática central; mostra desde o
  // primeiro acesso. Usuário pode desligar pelo toggle no ChatInput.
  const [debugMode, setDebugMode] = useState(true);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [stepIndex, setStepIndex] = useState(0);
  const [info, setInfo] = useState<ApiInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Trackeia quais eventos `agent_delivering_answer_to_user` (por índice na
  // lista de eventos do turno atual) já foram convertidos em bolha do
  // assistente no chat. Resetado a cada novo turno (sendMessage).
  // Necessário porque o backend agora emite MÚLTIPLAS entregas por turno
  // (texto pré-tool + texto pós-tool); cada uma vira uma bolha separada.
  const pushedDeliveriesRef = useRef<Set<number>>(new Set());

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
      // Novo turno → zera o tracker de entregas já empurradas
      pushedDeliveriesRef.current = new Set();

      const collected: AgentEvent[] = [];

      try {
        await streamChat(history, (ev) => {
          collected.push(ev);
          if (ev.type === "error") {
            const msg = String(ev.payload?.message ?? "erro desconhecido");
            setError(msg);
          }
        });

        // Coleta TODAS as entregas do turno (backend emite múltiplas: uma por
        // round de texto da LLM — ex.: texto pré-tool e depois texto pós-tool
        // viram 2 entregas separadas pra UI mostrar como bolhas distintas).
        const deliveryIndices: number[] = [];
        collected.forEach((ev, idx) => {
          if (ev.type === "agent_delivering_answer_to_user") {
            deliveryIndices.push(idx);
          }
        });

        // Fallback defensivo: se nenhuma entrega chegou (não deveria
        // acontecer com o agent.py refatorado, mas guardamos contra mismatch
        // de versão backend/frontend), tenta montar do texto bruto.
        if (deliveryIndices.length === 0 && collected.length === 0) {
          throw new Error("Stream vazio — agente não respondeu.");
        }
        if (deliveryIndices.length === 0) {
          const fallback = collected
            .filter((e) => e.type === "agent_received_text_from_llm")
            .map((e) => String(e.payload?.text ?? ""))
            .join("");
          if (fallback) {
            setMessages((prev) => [
              ...prev,
              { role: "assistant", content: fallback },
            ]);
          }
        } else if (!debugMode) {
          // Fora do debug, empurra todas as entregas de uma vez ao fim do stream.
          const newMsgs: ChatMessage[] = deliveryIndices.map((idx) => ({
            role: "assistant",
            content: String(collected[idx].payload?.text ?? ""),
          }));
          setMessages((prev) => [...prev, ...newMsgs]);
          deliveryIndices.forEach((idx) => pushedDeliveriesRef.current.add(idx));
        }
        // Em debug mode, NÃO empurra agora — o useEffect abaixo faz isso
        // progressivamente conforme o usuário avança no stepIndex.

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

  // Em debug mode, empurra mensagens do assistente progressivamente conforme
  // o stepIndex avança e passa por cada `agent_delivering_answer_to_user`.
  // Em modo normal as entregas foram empurradas todas em sendMessage; aqui é
  // no-op porque o Set já tem todos os índices.
  useEffect(() => {
    if (!debugMode || events.length === 0) return;
    const newMsgs: ChatMessage[] = [];
    for (let i = 0; i <= stepIndex && i < events.length; i++) {
      if (
        events[i].type === "agent_delivering_answer_to_user" &&
        !pushedDeliveriesRef.current.has(i)
      ) {
        pushedDeliveriesRef.current.add(i);
        newMsgs.push({
          role: "assistant",
          content: String(events[i].payload?.text ?? ""),
        });
      }
    }
    if (newMsgs.length > 0) {
      setMessages((prev) => [...prev, ...newMsgs]);
    }
  }, [stepIndex, debugMode, events]);

  return (
    <div className="flex h-screen flex-col">
      {/* Header slim — title + Limpar conversa agrupados à esquerda,
         provider badge à direita. Modo Debug saiu daqui pra dar espaço pro
         painel de debug se estender até o topo (foi pro ChatInput). */}
      <header className="border-b border-zinc-200 bg-white px-4 py-1.5 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Image
              src="/porto-inseguro-logo.jpg"
              alt="Logo Porto Inseguro (seguradora fictícia)"
              width={36}
              height={36}
              className="rounded-md object-contain"
              priority
            />
            <h1 className="text-base font-semibold text-zinc-900">
              InsurMind <span className="text-zinc-400">—</span>{" "}
              <span className="text-blue-700">Porto Inseguro</span>
            </h1>
            <span className="hidden text-xs text-zinc-500 md:inline">
              Seguro auto · I2A2 InsurMinds · seguradora <strong>fictícia</strong>
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setMessages([]);
                setEvents([]);
                setStepIndex(0);
                setError(null);
              }}
              className="h-7 gap-1.5 px-2 text-xs"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Limpar conversa
            </Button>
          </div>

          {info && (
            <Badge variant="outline" className="font-mono text-xs">
              {info.provider} · {info.tools.length} tools
            </Badge>
          )}
        </div>
      </header>

      {error && (
        <div className="border-b border-red-200 bg-red-50 px-6 py-2 text-sm text-red-800">
          ❌ {error}
        </div>
      )}

      {/* Conteúdo principal — chat ocupa 2/5 (antes 3/5), debug 3/5 (antes 2/5).
         Mais espaço pra timeline de eventos que é a parte mais densa. */}
      <main className="flex flex-1 overflow-hidden">
        {/* Chat */}
        <section
          className={`flex flex-col bg-white ${
            debugMode ? "w-2/5 border-r border-zinc-200" : "flex-1"
          }`}
        >
          <ChatMessages
            messages={messages}
            isLoading={isLoading}
            debugMode={debugMode}
            showPendingPlaceholder={!allRevealed}
          />
          <ChatInput
            onSend={sendMessage}
            disabled={isLoading}
            debugMode={debugMode}
            onDebugModeChange={setDebugMode}
          />
        </section>

        {/* Painel Debug (lateral) */}
        {debugMode && (
          <aside className="w-3/5">
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
