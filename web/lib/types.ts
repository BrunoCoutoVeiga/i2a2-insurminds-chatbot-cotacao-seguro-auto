/**
 * Tipos espelhando o backend Python (insurmind.events.AgentEvent).
 * Mantém em sincronia manualmente — se mudar lá, atualizar aqui.
 */

export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export type AgentEventType =
  | "llm_call_start"
  | "llm_text"
  | "tool_call_requested"
  | "tool_result"
  | "final_answer"
  | "error";

export interface AgentEvent {
  type: AgentEventType;
  payload: Record<string, unknown>;
  timestamp: string; // ISO format
}

/** Resposta do GET /api/info */
export interface ApiInfo {
  provider: string;
  tools: { name: string; description: string }[];
  cors_origins: string[];
}

/** Helpers de label/ícone pra cada tipo de evento (sincronizado com events.py) */
export const eventLabels: Record<AgentEventType, { short: string; tooltip: string }> = {
  llm_call_start: {
    short: "Enviar pergunta à LLM",
    tooltip:
      "A LLM vai ler o system prompt, as tools disponíveis e a sua pergunta. Decide o que fazer.",
  },
  llm_text: {
    short: "Receber texto da LLM",
    tooltip: "A LLM gerou um pedaço de texto (parte da resposta final).",
  },
  tool_call_requested: {
    short: "Executar tool pedida pela LLM",
    tooltip:
      "A LLM decidiu que precisa de uma informação que ela mesma não tem. Vou rodar a tool.",
  },
  tool_result: {
    short: "Devolver resultado da tool à LLM",
    tooltip:
      "Com o resultado da tool em mãos, a LLM vai formular a resposta final.",
  },
  final_answer: {
    short: "Mostrar resposta final ao usuário",
    tooltip:
      "A LLM tem todo o material e gerou o texto final. Vai aparecer no chat.",
  },
  error: {
    short: "Erro durante a execução",
    tooltip:
      "Alguma coisa deu errado — veja o detalhe e tente novamente.",
  },
};
