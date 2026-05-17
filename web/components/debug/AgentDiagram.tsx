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

interface Props {
  events: AgentEvent[];
  stepIndex: number;
}

/** IDs dos nodes — usados em activeNodes/activeEdges */
const NODE = {
  USER: "user",
  AGENT: "agent",
  LLM: "llm",
  RETRIEVE: "tool-retrieve_kb",
  QUOTE: "tool-compute_quote_mock",
  ESCALATE: "tool-escalar_humano",
  KB: "kb",
} as const;

/** IDs das edges */
const EDGE = {
  USER_AGENT: "user-agent",
  AGENT_LLM: "agent-llm",
  AGENT_RETRIEVE: "agent-retrieve",
  AGENT_QUOTE: "agent-quote",
  AGENT_ESCALATE: "agent-escalate",
  RETRIEVE_KB: "retrieve-kb",
  AGENT_USER: "agent-user",
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
  if (clean === "retrieve_kb") return NODE.RETRIEVE;
  if (clean === "compute_quote_mock") return NODE.QUOTE;
  if (clean === "escalar_humano") return NODE.ESCALATE;
  return null;
}

/** Calcula nodes e edges "ativos" pro evento atual */
function getActiveState(event: AgentEvent | null): {
  activeNodes: Set<string>;
  activeEdges: Set<string>;
} {
  const activeNodes = new Set<string>();
  const activeEdges = new Set<string>();
  if (!event) return { activeNodes, activeEdges };

  switch (event.type) {
    case "llm_call_start":
      activeNodes.add(NODE.USER);
      activeNodes.add(NODE.AGENT);
      activeNodes.add(NODE.LLM);
      activeEdges.add(EDGE.USER_AGENT);
      activeEdges.add(EDGE.AGENT_LLM);
      break;

    case "tool_call_requested": {
      const name = String(event.payload?.name ?? "");
      const nodeId = toolNodeId(name);
      activeNodes.add(NODE.LLM);
      activeNodes.add(NODE.AGENT);
      if (nodeId) {
        activeNodes.add(nodeId);
        if (nodeId === NODE.RETRIEVE) {
          activeEdges.add(EDGE.AGENT_RETRIEVE);
        } else if (nodeId === NODE.QUOTE) {
          activeEdges.add(EDGE.AGENT_QUOTE);
        } else if (nodeId === NODE.ESCALATE) {
          activeEdges.add(EDGE.AGENT_ESCALATE);
        }
      }
      activeEdges.add(EDGE.AGENT_LLM);
      break;
    }

    case "tool_result": {
      const name = String(event.payload?.name ?? "");
      const nodeId = toolNodeId(name);
      activeNodes.add(NODE.AGENT);
      if (nodeId) {
        activeNodes.add(nodeId);
        if (nodeId === NODE.RETRIEVE) {
          activeEdges.add(EDGE.AGENT_RETRIEVE);
          activeEdges.add(EDGE.RETRIEVE_KB);
          activeNodes.add(NODE.KB);
        } else if (nodeId === NODE.QUOTE) {
          activeEdges.add(EDGE.AGENT_QUOTE);
        } else if (nodeId === NODE.ESCALATE) {
          activeEdges.add(EDGE.AGENT_ESCALATE);
        }
      }
      break;
    }

    case "llm_text":
      activeNodes.add(NODE.AGENT);
      activeNodes.add(NODE.LLM);
      activeEdges.add(EDGE.AGENT_LLM);
      break;

    case "final_answer":
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

  const nodes: Node[] = useMemo(
    () => [
      {
        id: NODE.USER,
        position: { x: 0, y: 160 },
        data: { label: "👤 Usuário" },
        style: nodeStyle(activeNodes.has(NODE.USER), COLOR.USER),
        sourcePosition: Position.Right,
        targetPosition: Position.Right,
      },
      {
        id: NODE.AGENT,
        position: { x: 180, y: 160 },
        data: { label: "🤖 Agente\n(orquestrador)" },
        style: { ...nodeStyle(activeNodes.has(NODE.AGENT), COLOR.AGENT), whiteSpace: "pre-line" as const, minWidth: 150 },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      },
      {
        id: NODE.LLM,
        position: { x: 380, y: 30 },
        data: { label: "🧠 LLM" },
        style: nodeStyle(activeNodes.has(NODE.LLM), COLOR.LLM),
        sourcePosition: Position.Left,
        targetPosition: Position.Bottom,
      },
      {
        id: NODE.RETRIEVE,
        position: { x: 380, y: 120 },
        data: { label: "🔍 retrieve_kb" },
        style: nodeStyle(activeNodes.has(NODE.RETRIEVE), COLOR.TOOL),
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      },
      {
        id: NODE.QUOTE,
        position: { x: 380, y: 190 },
        data: { label: "💰 compute_quote" },
        style: nodeStyle(activeNodes.has(NODE.QUOTE), COLOR.TOOL),
        targetPosition: Position.Left,
      },
      {
        id: NODE.ESCALATE,
        position: { x: 380, y: 260 },
        data: { label: "📞 escalar_humano" },
        style: nodeStyle(activeNodes.has(NODE.ESCALATE), COLOR.TOOL),
        targetPosition: Position.Left,
      },
      {
        id: NODE.KB,
        position: { x: 600, y: 120 },
        data: { label: "🗄️ ChromaDB\n(KB vetorial)" },
        style: { ...nodeStyle(activeNodes.has(NODE.KB), COLOR.KB), whiteSpace: "pre-line" as const },
        targetPosition: Position.Left,
      },
    ],
    [activeNodes],
  );

  const edges: Edge[] = useMemo(() => {
    const make = (
      id: string,
      source: string,
      target: string,
      color: string,
    ): Edge => {
      const active = activeEdges.has(id);
      return {
        id,
        source,
        target,
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
    return [
      make(EDGE.USER_AGENT, NODE.USER, NODE.AGENT, COLOR.USER),
      make(EDGE.AGENT_LLM, NODE.AGENT, NODE.LLM, COLOR.LLM),
      make(EDGE.AGENT_RETRIEVE, NODE.AGENT, NODE.RETRIEVE, COLOR.TOOL),
      make(EDGE.AGENT_QUOTE, NODE.AGENT, NODE.QUOTE, COLOR.TOOL),
      make(EDGE.AGENT_ESCALATE, NODE.AGENT, NODE.ESCALATE, COLOR.TOOL),
      make(EDGE.RETRIEVE_KB, NODE.RETRIEVE, NODE.KB, COLOR.KB),
      {
        // Edge "agent → user" (resposta final) — desenhada por baixo dos outros
        id: EDGE.AGENT_USER,
        source: NODE.AGENT,
        target: NODE.USER,
        type: "bezier",
        animated: activeEdges.has(EDGE.AGENT_USER),
        style: {
          stroke: activeEdges.has(EDGE.AGENT_USER) ? COLOR.AGENT : "transparent",
          strokeWidth: activeEdges.has(EDGE.AGENT_USER) ? 2.5 : 0,
          opacity: activeEdges.has(EDGE.AGENT_USER) ? 1 : 0,
          transition: "all 200ms ease",
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: COLOR.AGENT,
          width: 18,
          height: 18,
        },
      },
    ];
  }, [activeEdges]);

  return (
    <div className="h-full w-full bg-white">
      <ReactFlow
        nodes={nodes}
        edges={edges}
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
