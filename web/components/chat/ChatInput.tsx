"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { useEffect, useRef, useState, KeyboardEvent } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
  debugMode: boolean;
  onDebugModeChange: (v: boolean) => void;
}

export function ChatInput({ onSend, disabled, debugMode, onDebugModeChange }: Props) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Foco inicial no input — usuário já pode começar a digitar sem clicar.
  // Também re-focar quando o input destrava (após resposta) pra fluir conversa.
  useEffect(() => {
    if (!disabled) inputRef.current?.focus();
  }, [disabled]);

  function handleSend() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex w-full items-center gap-2 border-t border-zinc-200 bg-white px-4 py-3">
      {/* Modo Debug toggle compact — vive aqui pra liberar espaço no header
         global, permitindo que o painel debug se estenda até o topo. */}
      <label
        className="flex cursor-pointer items-center gap-1.5 rounded-md border border-zinc-200 bg-zinc-50 px-2 py-1.5 text-xs hover:bg-zinc-100"
        title="Liga/desliga o painel passo-a-passo do agente"
      >
        <span>🪲</span>
        <span className="font-medium text-zinc-700">Debug</span>
        <Switch checked={debugMode} onCheckedChange={onDebugModeChange} />
      </label>
      <Input
        ref={inputRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKey}
        placeholder="Pergunte sobre seu seguro auto..."
        disabled={disabled}
        className="flex-1"
      />
      <Button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        className="bg-blue-600 hover:bg-blue-700 text-white"
      >
        Enviar
      </Button>
    </div>
  );
}
