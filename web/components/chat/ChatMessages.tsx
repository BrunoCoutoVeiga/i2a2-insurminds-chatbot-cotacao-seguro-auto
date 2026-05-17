"use client";

import { useEffect, useRef } from "react";
import { MessageBubble } from "./MessageBubble";
import type { ChatMessage } from "@/lib/types";

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
  debugMode: boolean;
  shouldHideLastAnswer: boolean;
}

export function ChatMessages({
  messages,
  isLoading,
  debugMode,
  shouldHideLastAnswer,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const showWelcome = messages.length === 0 && !isLoading;

  return (
    <div className="flex-1 min-h-0 overflow-y-auto">
      <div className="space-y-4 px-4 py-6">
        {showWelcome && (
          <MessageBubble
            message={{
              role: "assistant",
              content:
                "Olá! Eu sou o **InsurMind**, assistente da **Porto Inseguro** (seguradora fictícia) especializado em **seguro auto**. Posso te ajudar com:\n\n" +
                "- 📚 **Dúvidas** sobre cobertura, franquia, sinistro, condições da apólice\n" +
                "- 💰 **Cotação simulada** do seu seguro auto\n" +
                "- 📞 **Encaminhamento** pra atendimento humano se for outro produto\n\n" +
                "Como posso te ajudar hoje?",
            }}
          />
        )}

        {messages.map((m, i) => {
          const isLast = i === messages.length - 1;
          if (
            debugMode &&
            shouldHideLastAnswer &&
            m.role === "assistant" &&
            isLast
          ) {
            return (
              <div
                key={i}
                className="flex w-full items-start gap-3 justify-start"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-lg">
                  🚗
                </div>
                <div className="max-w-[80%] rounded-lg border border-blue-300 bg-blue-50 px-4 py-3 text-sm text-blue-900">
                  📍 <span className="font-medium">Modo Debug ativo</span> — clique
                  em <strong>▶ Próximo passo</strong> no painel lateral pra ver a
                  resposta aparecer.
                </div>
              </div>
            );
          }
          return <MessageBubble key={i} message={m} />;
        })}

        {isLoading && (
          <div className="flex w-full items-start gap-3 justify-start">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-lg">
              🚗
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3 text-sm text-zinc-500">
              <span className="inline-flex items-center gap-2">
                <span className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
                InsurMind pensando...
              </span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
