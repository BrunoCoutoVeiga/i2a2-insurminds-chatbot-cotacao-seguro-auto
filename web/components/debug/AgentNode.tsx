"use client";

/**
 * Custom node pro Agent. Default nodes do React Flow só têm 1 source e 1 target
 * handle (baseado em sourcePosition/targetPosition). Como o Agent precisa
 * conectar pra cima (LLM), pra direita (Tools) e receber da esquerda (User) +
 * de cima (LLM resposta), criamos 4 handles explícitos com IDs nomeados.
 *
 * Edges especificam qual handle usar via `sourceHandle` / `targetHandle`.
 */

import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { CSSProperties } from "react";

export type AgentNodeData = {
  label: string;
};

export function AgentNode({ data }: NodeProps) {
  const label = (data as AgentNodeData).label;
  // O style vem do array de nodes (definido no AgentDiagram), aplicado no wrapper
  // automaticamente pelo React Flow — não precisamos repetir aqui.
  return (
    <>
      {/* Handles INVISÍVEIS — o React Flow só os usa pra calcular o ponto de
         conexão das edges. Não precisam ter visual. */}
      <Handle
        type="target"
        position={Position.Left}
        id="from-user"
        style={hiddenHandle}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="to-tools"
        style={hiddenHandle}
      />
      <Handle
        type="source"
        position={Position.Top}
        id="to-llm"
        style={hiddenHandle}
      />
      <Handle
        type="target"
        position={Position.Top}
        id="from-llm"
        style={hiddenHandle}
      />
      <Handle
        type="source"
        position={Position.Left}
        id="to-user"
        style={hiddenHandle}
      />

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
