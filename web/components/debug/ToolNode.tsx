"use client";

/**
 * Custom node pras tools. Default nodes do React Flow só têm 1 source + 1
 * target — não dá pra ter "agente → tool" e "tool → agente" simultaneamente
 * pelo mesmo lado. Aqui criamos handles bidirecionais explícitos.
 *
 * Handles:
 *  - from-agent (target, esquerda)  — Agente → Tool
 *  - to-agent   (source, esquerda)  — Tool → Agente
 *  - to-kb      (source, direita)   — Tool → ChromaDB (só retrieve_kb usa)
 *  - from-kb    (target, direita)   — ChromaDB → Tool (só retrieve_kb usa)
 *
 * Handles sem edges conectadas ficam invisíveis e inertes.
 */

import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { CSSProperties } from "react";

export type ToolNodeData = {
  label: string;
};

export function ToolNode({ data }: NodeProps) {
  const label = (data as ToolNodeData).label;
  return (
    <>
      <Handle type="target" position={Position.Left} id="from-agent" style={hiddenHandle} />
      <Handle type="source" position={Position.Left} id="to-agent" style={hiddenHandle} />
      <Handle type="source" position={Position.Right} id="to-kb" style={hiddenHandle} />
      <Handle type="target" position={Position.Right} id="from-kb" style={hiddenHandle} />
      <div
        style={{
          whiteSpace: "pre-line",
          textAlign: "center",
          fontWeight: 500,
          fontSize: 13,
        }}
      >
        {label}
      </div>
    </>
  );
}

const hiddenHandle: CSSProperties = {
  opacity: 0,
  width: 1,
  height: 1,
  pointerEvents: "none",
};
