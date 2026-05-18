"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MarkerType,
  Position,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { AgentEvent } from "@/lib/types";
import { AgentNode } from "./AgentNode";
import { ToolNode } from "./ToolNode";
import { RagBadgeNode } from "./RagBadgeNode";

const nodeTypes = { agent: AgentNode, tool: ToolNode, ragBadge: RagBadgeNode };

interface Props {
  events: AgentEvent[];
  stepIndex: number;
}

/** IDs dos nodes — usados em activeNodes/activeEdges */
const NODE = {
  USER: "user",
  AGENT: "agent",
  LLM: "llm",
  RETRIEVE: "tool-consultar",
  QUOTE: "tool-cotar",
  ESCALATE: "tool-encaminhar",
  KB: "kb",
} as const;

/** IDs das edges — pares bidirecionais (forward/reverse) entre os nodes
    conectados. Cada passo do agente ativa só uma direção, e a outra fica
    invisível pra não poluir o diagrama. */
const EDGE = {
  USER_AGENT: "user-agent",       // user → agent (passo 1)
  AGENT_LLM: "agent-llm",         // agent → llm (passos 2 e 6)
  LLM_AGENT: "llm-agent",         // llm → agent (passos 3 e 7)
  AGENT_RETRIEVE: "agent-retrieve",
  RETRIEVE_AGENT: "retrieve-agent",
  AGENT_QUOTE: "agent-quote",
  QUOTE_AGENT: "quote-agent",
  AGENT_ESCALATE: "agent-escalate",
  ESCALATE_AGENT: "escalate-agent",
  RETRIEVE_KB: "retrieve-kb",     // retrieve_kb → ChromaDB (consulta vetorial)
  KB_RETRIEVE: "kb-retrieve",     // ChromaDB → retrieve_kb (chunks de volta)
  AGENT_USER: "agent-user",       // agent → user (passo 8 — resposta final)
} as const;

/** Normaliza nome de tool: remove prefixo MCP do Claude SDK */
function normalizeToolName(name: string): string | null {
  // Filtra ToolSearch interno do MCP
  if (name === "ToolSearch" || name.includes("ToolSearch")) return null;
  // Remove prefixo mcp__insurmind__
  const clean = name.replace(/^mcp__insurmind__/, "");
  return clean || null;
}

/** Mapeia nome de tool → ID do node */
function toolNodeId(toolName: string): string | null {
  const clean = normalizeToolName(toolName);
  if (!clean) return null;
  // Backend tool names (atualizados em 2026-05-18 pra remover info disclosure
  // — ver RELATORIO.md sessão "Hardening anti-prompt-injection").
  if (clean === "consultar_porto_inseguro") return NODE.RETRIEVE;
  if (clean === "cotar_seguro_auto") return NODE.QUOTE;
  if (clean === "encaminhar_atendimento") return NODE.ESCALATE;
  // Compat: aceita também os nomes antigos (caso versão antiga do backend
  // ainda esteja rodando — debug ainda funciona).
  if (clean === "retrieve_kb") return NODE.RETRIEVE;
  if (clean === "compute_quote_mock") return NODE.QUOTE;
  if (clean === "escalar_humano") return NODE.ESCALATE;
  return null;
}

/** Calcula nodes e edges "ativos" pro evento atual.
    Mapeamento agente-centric — cada tipo de evento destaca o subset de
    componentes envolvidos naquela ação específica do Agente. */
function getActiveState(event: AgentEvent | null): {
  activeNodes: Set<string>;
  activeEdges: Set<string>;
} {
  const activeNodes = new Set<string>();
  const activeEdges = new Set<string>();
  if (!event) return { activeNodes, activeEdges };

  // Helper pra adicionar tool node + edge agent→tool (direção FORWARD)
  const addToolForward = (name: string) => {
    const nodeId = toolNodeId(name);
    if (!nodeId) return;
    activeNodes.add(nodeId);
    if (nodeId === NODE.RETRIEVE) activeEdges.add(EDGE.AGENT_RETRIEVE);
    else if (nodeId === NODE.QUOTE) activeEdges.add(EDGE.AGENT_QUOTE);
    else if (nodeId === NODE.ESCALATE) activeEdges.add(EDGE.AGENT_ESCALATE);
    return nodeId;
  };

  // Helper pra direção REVERSE (tool → agent)
  const addToolReverse = (name: string) => {
    const nodeId = toolNodeId(name);
    if (!nodeId) return;
    activeNodes.add(nodeId);
    if (nodeId === NODE.RETRIEVE) activeEdges.add(EDGE.RETRIEVE_AGENT);
    else if (nodeId === NODE.QUOTE) activeEdges.add(EDGE.QUOTE_AGENT);
    else if (nodeId === NODE.ESCALATE) activeEdges.add(EDGE.ESCALATE_AGENT);
    return nodeId;
  };

  switch (event.type) {
    case "agent_received_user_input":
      // Passo 1: User → Agent (Agente recebendo o input)
      activeNodes.add(NODE.USER);
      activeNodes.add(NODE.AGENT);
      activeEdges.add(EDGE.USER_AGENT);
      break;

    case "agent_sending_to_llm":
      // Passo 2: Agent → LLM (enviando contexto)
      activeNodes.add(NODE.AGENT);
      activeNodes.add(NODE.LLM);
      activeEdges.add(EDGE.AGENT_LLM);
      break;

    case "agent_received_tool_request_from_llm": {
      // Passo 3: LLM → Agent (vindo o pedido de tool)
      activeNodes.add(NODE.LLM);
      activeNodes.add(NODE.AGENT);
      activeEdges.add(EDGE.LLM_AGENT);
      break;
    }

    case "agent_executing_tool": {
      // Passo 4: Agent → Tool (rodando); inclui retrieve_kb → ChromaDB
      const name = String(event.payload?.name ?? "");
      activeNodes.add(NODE.AGENT);
      const nodeId = addToolForward(name);
      if (nodeId === NODE.RETRIEVE) {
        activeNodes.add(NODE.KB);
        activeEdges.add(EDGE.RETRIEVE_KB);
      }
      break;
    }

    case "agent_received_tool_result": {
      // Passo 5: Tool → Agent (resultado voltando); ChromaDB → retrieve_kb
      const name = String(event.payload?.name ?? "");
      activeNodes.add(NODE.AGENT);
      const nodeId = addToolReverse(name);
      if (nodeId === NODE.RETRIEVE) {
        activeNodes.add(NODE.KB);
        activeEdges.add(EDGE.KB_RETRIEVE);
      }
      break;
    }

    case "agent_sending_tool_result_to_llm":
      // Passo 6: Agent → LLM (devolvendo resultado da tool)
      activeNodes.add(NODE.AGENT);
      activeNodes.add(NODE.LLM);
      activeEdges.add(EDGE.AGENT_LLM);
      break;

    case "agent_received_text_from_llm":
      // Passo 7: LLM → Agent (recebendo texto da LLM)
      activeNodes.add(NODE.AGENT);
      activeNodes.add(NODE.LLM);
      activeEdges.add(EDGE.LLM_AGENT);
      break;

    case "agent_delivering_answer_to_user":
      // Passo 8: Agent → User (apresentando ao usuário)
      activeNodes.add(NODE.AGENT);
      activeNodes.add(NODE.USER);
      activeEdges.add(EDGE.AGENT_USER);
      break;

    case "error":
      // Nada highlight — só caracter
      break;
  }
  return { activeNodes, activeEdges };
}

// =============================================================================
// Estilos dos nodes (helper)
// =============================================================================

function nodeStyle(active: boolean, color: string) {
  return {
    background: active ? color : "#f4f4f5",
    color: active ? "#fff" : "#a1a1aa",
    border: active ? `2px solid ${color}` : "1px solid #d4d4d8",
    borderRadius: 10,
    padding: "8px 12px",
    fontSize: 13,
    fontWeight: 500 as const,
    boxShadow: active
      ? `0 0 0 4px ${color}33, 0 4px 12px ${color}44`
      : "none",
    transition: "all 200ms ease",
    opacity: active ? 1 : 0.6,
    minWidth: 130,
    textAlign: "center" as const,
  };
}

// =============================================================================
// Layout estático (coordenadas em pixels)
// =============================================================================

const COLOR = {
  USER: "#0ea5e9",     // sky-500
  AGENT: "#2563eb",    // blue-600
  LLM: "#7c3aed",      // violet-600
  TOOL: "#059669",     // emerald-600
  KB: "#d97706",       // amber-600
};

// =============================================================================
// Componente
// =============================================================================

export function AgentDiagram({ events, stepIndex }: Props) {
  const currentEvent = events[stepIndex] ?? null;
  const { activeNodes, activeEdges } = useMemo(
    () => getActiveState(currentEvent),
    [currentEvent],
  );

  // RAG zone fica "active" só quando a ação está acontecendo DENTRO da zona
  // visual (retrieve_kb + ChromaDB):
  //   4. agent_executing_tool       (retrieval acontecendo na KB)
  //   5. agent_received_tool_result (chunks voltaram da KB)
  //
  // No passo 6 (agent_sending_tool_result_to_llm) a ação se move pra fora da
  // zona — está entre Agent e LLM. Deixar aceso ali seria visualmente
  // inconsistente com a animação principal do diagrama.
  const ragActive = useMemo(() => {
    if (!currentEvent) return false;
    const ragSteps = new Set([
      "agent_executing_tool",
      "agent_received_tool_result",
    ]);
    if (!ragSteps.has(currentEvent.type)) return false;
    const name = normalizeToolName(String(currentEvent.payload?.name ?? ""));
    // Aceita nome novo + compat com antigo (versão pré-2026-05-18).
    return name === "consultar_porto_inseguro" || name === "retrieve_kb";
  }, [currentEvent]);

  const nodes: Node[] = useMemo(
    () => [
      {
        // Badge decorativo "🧠 RAG" envolvendo retrieve_kb + ChromaDB.
        // PRIMEIRO no array pra renderizar atrás dos demais nodes.
        // Sem pointerEvents → não bloqueia interação com os nodes internos.
        id: "rag-badge",
        type: "ragBadge",
        position: { x: 410, y: 100 },
        data: { active: ragActive, width: 420, height: 100 },
        draggable: false,
        selectable: false,
        style: { zIndex: -1 },
      },
      {
        id: NODE.USER,
        position: { x: 0, y: 200 },
        data: { label: "👤 Usuário" },
        style: nodeStyle(activeNodes.has(NODE.USER), COLOR.USER),
        sourcePosition: Position.Right,
        targetPosition: Position.Right,
      },
      {
        // Agent é custom node: tem 4 handles nomeados (from-user, to-tools,
        // to-llm, from-llm, to-user) pra suportar conexões em todas as direções.
        id: NODE.AGENT,
        type: "agent",
        position: { x: 200, y: 200 },
        data: { label: "🤖 Agente\n(orquestrador)" },
        style: {
          ...nodeStyle(activeNodes.has(NODE.AGENT), COLOR.AGENT),
          minWidth: 150,
        },
      },
      {
        // LLM EM CIMA do Agent (mesma coluna X aproximada)
        id: NODE.LLM,
        position: { x: 215, y: 50 },
        data: { label: "🧠 LLM" },
        style: nodeStyle(activeNodes.has(NODE.LLM), COLOR.LLM),
        sourcePosition: Position.Bottom,
        targetPosition: Position.Bottom,
      },
      {
        // Tool nodes: custom ToolNode com handles bidirecionais explícitos
        // (from-agent, to-agent, to-kb, from-kb). Handles sem edges conectadas
        // ficam invisíveis — compute_quote e escalar_humano não usam to-kb/from-kb.
        id: NODE.RETRIEVE,
        type: "tool",
        position: { x: 430, y: 130 },
        data: { label: "🔍 Consultar base" },
        style: nodeStyle(activeNodes.has(NODE.RETRIEVE), COLOR.TOOL),
      },
      {
        id: NODE.QUOTE,
        type: "tool",
        position: { x: 430, y: 200 },
        data: { label: "💰 Cotar seguro" },
        style: nodeStyle(activeNodes.has(NODE.QUOTE), COLOR.TOOL),
      },
      {
        id: NODE.ESCALATE,
        type: "tool",
        position: { x: 430, y: 270 },
        data: { label: "📞 Atendimento humano" },
        style: nodeStyle(activeNodes.has(NODE.ESCALATE), COLOR.TOOL),
      },
      {
        // ChromaDB: reusa ToolNode (mesma necessidade de handles
        // bidirecionais na esquerda — recebe consulta do retrieve_kb e
        // devolve chunks). Os handles to-kb/from-kb da direita ficam unused.
        id: NODE.KB,
        type: "tool",
        position: { x: 660, y: 130 },
        data: { label: "🗄️ ChromaDB\n(KB vetorial)" },
        style: { ...nodeStyle(activeNodes.has(NODE.KB), COLOR.KB), whiteSpace: "pre-line" as const },
      },
    ],
    [activeNodes, ragActive],
  );

  const edges: Edge[] = useMemo(() => {
    // Edge "schema" — sempre renderizada, fica cinza quando inativa, colorida
    // quando ativa. Usada pras edges FORWARD (que formam o esqueleto do diagrama).
    const make = (
      id: string,
      source: string,
      target: string,
      color: string,
      sourceHandle?: string,
      targetHandle?: string,
    ): Edge => {
      const active = activeEdges.has(id);
      return {
        id,
        source,
        target,
        sourceHandle,
        targetHandle,
        animated: active,
        style: {
          stroke: active ? color : "#d4d4d8",
          strokeWidth: active ? 2.5 : 1,
          opacity: active ? 1 : 0.4,
          transition: "all 200ms ease",
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: active ? color : "#d4d4d8",
          width: 18,
          height: 18,
        },
      };
    };

    // Edge "directional" — só aparece quando ativa. Usada pras REVERSE
    // (LLM→Agent, Tool→Agent, KB→Retrieve, Agent→User) pra não poluir o
    // diagrama em idle com setas duplas. Quando ativa, mostra a seta na
    // direção correta do fluxo do passo.
    const makeReverse = (
      id: string,
      source: string,
      target: string,
      color: string,
      sourceHandle?: string,
      targetHandle?: string,
    ): Edge => {
      const active = activeEdges.has(id);
      return {
        id,
        source,
        target,
        sourceHandle,
        targetHandle,
        animated: active,
        style: {
          stroke: active ? color : "transparent",
          strokeWidth: active ? 2.5 : 0,
          opacity: active ? 1 : 0,
          transition: "all 200ms ease",
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color,
          width: 18,
          height: 18,
        },
      };
    };

    return [
      // === FORWARD edges (schema — sempre desenhadas, faded quando inativas) ===
      // User → Agent (entra pela esquerda do Agent)
      make(EDGE.USER_AGENT, NODE.USER, NODE.AGENT, COLOR.USER, undefined, "from-user"),
      // Agent → LLM (sai pelo TOPO do Agent, entra pelo bottom do LLM)
      make(EDGE.AGENT_LLM, NODE.AGENT, NODE.LLM, COLOR.LLM, "to-llm"),
      // Agent → Tools (sai pela direita do Agent, entra na esquerda da tool)
      make(EDGE.AGENT_RETRIEVE, NODE.AGENT, NODE.RETRIEVE, COLOR.TOOL, "to-tools", "from-agent"),
      make(EDGE.AGENT_QUOTE, NODE.AGENT, NODE.QUOTE, COLOR.TOOL, "to-tools", "from-agent"),
      make(EDGE.AGENT_ESCALATE, NODE.AGENT, NODE.ESCALATE, COLOR.TOOL, "to-tools", "from-agent"),
      // retrieve_kb → ChromaDB (consulta vetorial)
      make(EDGE.RETRIEVE_KB, NODE.RETRIEVE, NODE.KB, COLOR.KB, "to-kb", "from-agent"),

      // === REVERSE edges (só aparecem quando o passo ativa a direção contrária) ===
      // LLM → Agent (passos 3 e 7: agente recebe da LLM)
      makeReverse(EDGE.LLM_AGENT, NODE.LLM, NODE.AGENT, COLOR.LLM, undefined, "from-llm"),
      // Tool → Agent (passo 5: agente recebe resultado da tool)
      makeReverse(EDGE.RETRIEVE_AGENT, NODE.RETRIEVE, NODE.AGENT, COLOR.TOOL, "to-agent", "from-tools"),
      makeReverse(EDGE.QUOTE_AGENT, NODE.QUOTE, NODE.AGENT, COLOR.TOOL, "to-agent", "from-tools"),
      makeReverse(EDGE.ESCALATE_AGENT, NODE.ESCALATE, NODE.AGENT, COLOR.TOOL, "to-agent", "from-tools"),
      // ChromaDB → retrieve_kb (chunks de volta após consulta)
      makeReverse(EDGE.KB_RETRIEVE, NODE.KB, NODE.RETRIEVE, COLOR.KB, "to-agent", "from-kb"),
      // Agent → User (passo 8 — resposta final, sai pela esquerda do Agent)
      makeReverse(EDGE.AGENT_USER, NODE.AGENT, NODE.USER, COLOR.AGENT, "to-user"),
    ];
  }, [activeEdges]);

  return (
    <div className="h-full w-full bg-white">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.05, minZoom: 0.5, maxZoom: 1.5 }}
        minZoom={0.3}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
      >
        <Background gap={16} size={1} color="#e4e4e7" />
        <Controls showInteractive={false} position="bottom-right" />
      </ReactFlow>
    </div>
  );
}
