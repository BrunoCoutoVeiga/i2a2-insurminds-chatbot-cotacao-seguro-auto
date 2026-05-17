/**
 * Tipos espelhando o backend Python (insurmind.events.AgentEvent).
 * Mantém em sincronia manualmente — se mudar lá, atualizar aqui.
 *
 * Todos os eventos são narrados na perspectiva do Agente — ele é o ator
 * central. Sequência típica de uma FAQ (com tool): 8 passos.
 * Off-domain (LLM responde direto sem tool): só 4 passos (1, 2, 7, 8).
 */

export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export type AgentEventType =
  | "agent_received_user_input"
  | "agent_sending_to_llm"
  | "agent_received_tool_request_from_llm"
  | "agent_executing_tool"
  | "agent_received_tool_result"
  | "agent_sending_tool_result_to_llm"
  | "agent_received_text_from_llm"
  | "agent_delivering_answer_to_user"
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

/** Labels pros botões "Próximo passo" + tooltips didáticos.
    Mantenha em sincronia com events.py::AgentEvent.short_description. */
export const eventLabels: Record<AgentEventType, { short: string; tooltip: string }> = {
  agent_received_user_input: {
    short: "Agente recebendo pergunta do usuário",
    tooltip:
      "O Agente recebeu o prompt do usuário e está preparando o contexto da " +
      "conversa (histórico + nova mensagem) pra enviar à LLM no próximo passo.",
  },
  agent_sending_to_llm: {
    short: "Agente enviando contexto à LLM",
    tooltip:
      "O Agente vai concatenar o prompt do usuário, o system prompt (instruções " +
      "de comportamento) e a lista de tools disponíveis, e enviar tudo pra LLM " +
      "processar. A LLM decide a partir disso se responde direto ou chama tool.",
  },
  agent_received_tool_request_from_llm: {
    short: "Agente recebeu pedido de tool",
    tooltip:
      "A LLM decidiu que precisa de uma informação que ela mesma não tem (ex.: " +
      "consulta na base de conhecimento, cotação) e pediu pro Agente executar " +
      "uma tool específica com determinados parâmetros.",
  },
  agent_executing_tool: {
    short: "Agente executando a tool",
    tooltip:
      "O Agente está rodando a função Python da tool pedida pela LLM (ex.: " +
      "retrieve_kb busca chunks no Chroma; compute_quote_mock calcula prêmios).",
  },
  agent_received_tool_result: {
    short: "Agente recebeu resultado da tool",
    tooltip:
      "A tool terminou de executar e devolveu um resultado em texto.",
  },
  agent_sending_tool_result_to_llm: {
    short: "Agente devolvendo resultado à LLM",
    tooltip:
      "Com o resultado da tool em mãos, o Agente vai enviar de volta pra LLM " +
      "junto com o histórico, pra ela formular a resposta final em linguagem " +
      "natural ao usuário.",
  },
  agent_received_text_from_llm: {
    short: "Agente recebeu texto da LLM",
    tooltip:
      "A LLM gerou um pedaço de texto. Pode ser a resposta direta (quando " +
      "não pediu tool — caso off-domain) ou a resposta final (depois de " +
      "incorporar o resultado da tool).",
  },
  agent_delivering_answer_to_user: {
    short: "Agente apresentando resposta ao usuário",
    tooltip:
      "O Agente vai mostrar o texto final da LLM ao usuário no chat da UI.",
  },
  error: {
    short: "Erro durante a execução",
    tooltip:
      "Alguma coisa deu errado — veja o detalhe e tente novamente.",
  },
};
