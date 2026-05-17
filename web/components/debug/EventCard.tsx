"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, ChevronRight, CheckCircle2, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { eventLabels, type AgentEvent } from "@/lib/types";

interface Props {
  index: number;
  event: AgentEvent;
  isCurrent: boolean;
}

export function EventCard({ index, event, isCurrent }: Props) {
  const [expanded, setExpanded] = useState(isCurrent);
  const [showJson, setShowJson] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  // Sincroniza expansão com isCurrent: passo atual abre, anteriores colapsam.
  // O usuário ainda pode re-expandir manualmente um passo anterior — mas ao
  // avançar pro próximo, a UI volta a focar só no atual pra não saturar.
  useEffect(() => {
    setExpanded(isCurrent);
  }, [isCurrent]);

  // Scroll automático: quando o card vira atual, alinha o TOPO dela com o
  // topo do scroll container — assim o usuário vê o passo do início, mesmo
  // se o conteúdo for maior que a viewport.
  //
  // `requestAnimationFrame` é crucial: sem ele, o scroll roda no mesmo tick
  // em que setExpanded(true) foi chamado, ANTES do React reflowar o layout
  // com a nova altura do card. Resultado: posiciona com altura antiga
  // (colapsada), depois o card cresce e o título sai da viewport. Esperar 1
  // frame garante que o reflow já aconteceu.
  useEffect(() => {
    if (isCurrent && cardRef.current) {
      const id = requestAnimationFrame(() => {
        cardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      return () => cancelAnimationFrame(id);
    }
  }, [isCurrent]);

  // Fallback defensivo: se o backend emitir um tipo desconhecido (ex.: agent.py
  // ainda rodando com versão antiga após edit no events.py), não quebra a UI.
  const label = eventLabels[event.type] ?? {
    short: event.type,
    tooltip: "Evento de tipo desconhecido — backend pode estar desatualizado.",
  };

  const Icon = isCurrent ? Loader2 : CheckCircle2;
  const iconClass = isCurrent
    ? "text-amber-500 animate-pulse"
    : "text-emerald-600";
  const borderClass = isCurrent
    ? "border-amber-300 bg-amber-50/40"
    : "border-emerald-200 bg-white";

  const time = new Date(event.timestamp).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <div ref={cardRef} className="scroll-mt-2">
      <Card className={cn("border", borderClass, "transition-colors")}>
      <button
        type="button"
        onClick={() => setExpanded((x) => !x)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-zinc-50"
      >
        <Icon className={cn("h-4 w-4 shrink-0", iconClass)} />
        <span className="font-medium text-zinc-700">Passo {index + 1}</span>
        <span className="text-zinc-400">—</span>
        <span className="text-zinc-700 flex-1">{label.short}</span>
        {expanded ? (
          <ChevronDown className="h-4 w-4 text-zinc-400" />
        ) : (
          <ChevronRight className="h-4 w-4 text-zinc-400" />
        )}
      </button>

      {expanded && (
        <div className="border-t border-zinc-200 px-3 py-3 text-sm">
          {/* Descrição didática */}
          <div className="mb-3 rounded bg-blue-50 border border-blue-200 px-3 py-2 text-xs text-blue-900">
            {label.tooltip}
          </div>

          <PayloadDetails event={event} />

          <div className="mt-3 flex items-center justify-between gap-2 text-xs text-zinc-500">
            <span>
              ⏱️ {time} &nbsp;|&nbsp; <code>{event.type}</code>
            </span>
            <button
              type="button"
              onClick={() => setShowJson((x) => !x)}
              className="text-blue-600 hover:underline"
            >
              {showJson ? "esconder" : "🔍 ver"} formato técnico (JSON)
            </button>
          </div>

          {showJson && (
            <pre className="mt-2 overflow-x-auto rounded bg-zinc-100 p-2 text-xs text-zinc-700">
              {JSON.stringify(event, null, 2)}
            </pre>
          )}
        </div>
      )}
      </Card>
    </div>
  );
}

function PayloadDetails({ event }: { event: AgentEvent }) {
  const p = event.payload;
  switch (event.type) {
    case "agent_received_user_input":
      return (
        <div className="space-y-2">
          <div>
            <span className="text-zinc-500">Mensagem recebida do usuário:</span>{" "}
            <code className="rounded bg-zinc-100 px-1 py-0.5 text-zinc-700">
              {String(p.user_message ?? "")}
            </code>
          </div>
          <div>
            <span className="text-zinc-500">Tamanho do histórico:</span>{" "}
            <span className="text-zinc-700">
              {String(p.history_length ?? 1)} mensagem
              {Number(p.history_length ?? 1) > 1 ? "s" : ""} (incluindo esta nova)
            </span>
          </div>
        </div>
      );

    case "agent_sending_to_llm": {
      const tools = (p.tools_available as { name: string; description: string }[]) ?? [];
      return (
        <div className="space-y-2">
          <div className="text-zinc-500">O Agente está enviando à LLM:</div>
          <ul className="ml-4 list-disc text-zinc-700 space-y-1">
            <li>
              <strong>System prompt</strong> (instruções de comportamento, persona,
              regras, escopo).{" "}
              <details className="inline">
                <summary className="cursor-pointer text-blue-600 hover:underline inline">
                  ver texto
                </summary>
                <pre className="mt-1 overflow-x-auto rounded bg-zinc-100 p-2 text-xs text-zinc-700 whitespace-pre-wrap">
                  {String(p.system_prompt_full ?? "")}
                </pre>
              </details>
            </li>
            <li>
              <strong>Mensagem do usuário:</strong>{" "}
              <code className="rounded bg-zinc-100 px-1 py-0.5">
                {String(p.user_message ?? "")}
              </code>
            </li>
            <li>
              <strong>Histórico:</strong> {String(p.history_length ?? 1)} mensagem(ns)
            </li>
            <li>
              <strong>Tools disponíveis ({tools.length}):</strong>
              <ul className="ml-4 mt-1 list-[circle] text-zinc-700">
                {tools.map((t) => (
                  <li key={t.name}>
                    <code>{t.name}</code> — {t.description}
                  </li>
                ))}
              </ul>
            </li>
          </ul>
        </div>
      );
    }

    case "agent_received_tool_request_from_llm":
    case "agent_executing_tool": {
      const args = (p.args as Record<string, unknown>) ?? {};
      return (
        <div className="space-y-2">
          <div>
            <span className="text-zinc-500">Tool:</span>{" "}
            <code className="rounded bg-zinc-100 px-1 py-0.5 font-mono text-zinc-700">
              {String(p.name)}
            </code>
          </div>
          <div>
            <span className="text-zinc-500">Parâmetros:</span>
            <ul className="ml-4 mt-1 list-disc text-zinc-700">
              {Object.entries(args).map(([k, v]) => (
                <li key={k}>
                  <code>{k}</code> = <code>{JSON.stringify(v)}</code>
                </li>
              ))}
            </ul>
          </div>
        </div>
      );
    }

    case "agent_received_tool_result": {
      const preview = String(p.result_preview ?? "");
      return (
        <div className="space-y-2">
          <div>
            <span className="text-zinc-500">Resultado da tool</span>{" "}
            <code>{String(p.name)}</code>:
          </div>
          <pre className="overflow-x-auto rounded bg-zinc-100 p-2 text-xs text-zinc-700 whitespace-pre-wrap">
            {preview}
          </pre>
        </div>
      );
    }

    case "agent_sending_tool_result_to_llm":
      return (
        <div>
          <span className="text-zinc-500">
            Devolvendo o resultado da tool{" "}
            <code>{String(p.name)}</code> pra LLM. Ela vai formular a resposta
            final ao usuário incorporando essa informação.
          </span>
        </div>
      );

    case "agent_received_text_from_llm": {
      const text = String(p.text ?? "");
      return (
        <div>
          <div className="text-zinc-500">LLM gerou este texto:</div>
          <pre className="mt-1 overflow-x-auto rounded bg-zinc-100 p-2 text-xs text-zinc-700 whitespace-pre-wrap">
            {text.length > 500 ? text.slice(0, 500) + "..." : text}
          </pre>
        </div>
      );
    }

    case "agent_delivering_answer_to_user": {
      const text = String(p.text ?? "");
      return (
        <div className="space-y-2">
          <div className="rounded bg-emerald-50 border border-emerald-200 px-3 py-2 text-emerald-800 text-xs">
            ✅ Resposta final pronta — apareceu no chat.
          </div>
          <div className="text-zinc-600">
            {text.length > 300 ? text.slice(0, 300) + "..." : text}
          </div>
        </div>
      );
    }

    case "error":
      return (
        <div className="rounded bg-red-50 border border-red-200 px-3 py-2 text-red-800 text-xs">
          ❌ <strong>{String(p.message ?? "Erro desconhecido")}</strong>
        </div>
      );

    default:
      return null;
  }
}
