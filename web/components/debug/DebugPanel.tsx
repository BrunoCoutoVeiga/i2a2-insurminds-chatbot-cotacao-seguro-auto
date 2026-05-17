"use client";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { eventLabels, type AgentEvent } from "@/lib/types";
import { EventCard } from "./EventCard";

interface Props {
  events: AgentEvent[];
  stepIndex: number;
  onNext: () => void;
  onSkipToEnd: () => void;
}

export function DebugPanel({ events, stepIndex, onNext, onSkipToEnd }: Props) {
  const total = events.length;
  const allRevealed = stepIndex >= total - 1;
  const remaining = Math.max(0, total - stepIndex - 1);
  const nextEvent = !allRevealed ? events[stepIndex + 1] : null;

  return (
    <div className="flex h-full flex-col bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🪲</span>
          <h2 className="text-base font-semibold text-zinc-800">
            Painel Debug — passo a passo
          </h2>
        </div>
        <p className="mt-1 text-xs text-zinc-500">
          Cada passo do agente aparece conforme você clica em{" "}
          <strong>▶ Próximo passo</strong>. (Fase 3 trará o diagrama animado
          de componentes.)
        </p>
      </header>

      <ScrollArea className="flex-1 px-3 py-3">
        {events.length === 0 ? (
          <div className="rounded border border-dashed border-zinc-300 bg-white px-4 py-8 text-center text-sm text-zinc-500">
            Faça uma pergunta no chat ao lado pra ver os passos do agente
            aparecerem aqui.
          </div>
        ) : (
          <div className="space-y-2">
            {events.slice(0, stepIndex + 1).map((ev, i) => (
              <EventCard
                key={i}
                index={i}
                event={ev}
                isCurrent={i === stepIndex && !allRevealed}
              />
            ))}
          </div>
        )}
      </ScrollArea>

      {events.length > 0 && (
        <footer className="border-t border-zinc-200 bg-white px-3 py-3 space-y-2">
          {nextEvent ? (
            <>
              <Button
                onClick={onNext}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              >
                ▶ Passo {stepIndex + 2}: {eventLabels[nextEvent.type].short}
              </Button>
              {remaining > 1 && (
                <Button
                  onClick={onSkipToEnd}
                  variant="outline"
                  className="w-full"
                >
                  ⏩ Rodar até o final ({remaining} passos restantes)
                </Button>
              )}
            </>
          ) : (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-center text-sm text-emerald-800">
              ✅ Conversa nesse turno concluída — pronto pra próxima pergunta.
            </div>
          )}
        </footer>
      )}
    </div>
  );
}
