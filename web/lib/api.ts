/**
 * Cliente da API FastAPI do InsurMind.
 *
 * Parser de SSE manual porque `EventSource` nativo do browser só suporta GET
 * (nosso /api/chat é POST com body JSON). Usa `fetch()` + `ReadableStream`.
 */

import type { AgentEvent, ApiInfo, ChatMessage } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export async function fetchInfo(): Promise<ApiInfo> {
  const res = await fetch(`${API_BASE}/api/info`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API /api/info HTTP ${res.status}`);
  return res.json();
}

/**
 * POST /api/chat com SSE streaming. Chama `onEvent` pra cada AgentEvent recebido.
 * Retorna Promise<void> que resolve quando o stream termina (ou rejeita em erro).
 */
export async function streamChat(
  messages: ChatMessage[],
  onEvent: (ev: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ messages }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "(sem body)");
    throw new Error(`API /api/chat HTTP ${res.status}: ${text}`);
  }
  if (!res.body) {
    throw new Error("API /api/chat não retornou body");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE messages são separadas por \n\n (ou \r\n\r\n em alguns servidores)
    let sepIdx;
    while ((sepIdx = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, sepIdx);
      buffer = buffer.slice(sepIdx + 2);
      const ev = parseSseMessage(raw);
      if (ev) onEvent(ev);
    }
  }
  // Flush qualquer evento pendente no buffer (raro)
  if (buffer.trim()) {
    const ev = parseSseMessage(buffer);
    if (ev) onEvent(ev);
  }
}

function parseSseMessage(raw: string): AgentEvent | null {
  const lines = raw.split(/\r?\n/);
  let dataLines: string[] = [];
  let eventType: string | null = null;
  for (const line of lines) {
    if (line.startsWith(":")) continue; // SSE comment
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }
  const dataStr = dataLines.join("\n");
  if (!dataStr) return null;
  try {
    const parsed = JSON.parse(dataStr);
    // O backend sempre inclui {type, payload, timestamp} no JSON.
    // Usamos `eventType` do header SSE como fallback caso o JSON esteja malformado.
    return parsed as AgentEvent;
  } catch (err) {
    console.warn("SSE parse failure:", err, dataStr);
    return null;
  }
}
