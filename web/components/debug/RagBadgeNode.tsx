"use client";

/**
 * Node decorativo que destaca a "zona RAG" do diagrama — envolve retrieve_kb
 * + ChromaDB com uma borda tracejada e uma etiqueta no topo explicando o que
 * é RAG. Razão didática: alunos do curso procuram "onde está o RAG" no
 * sistema, e visualmente delimitar a zona ajuda a fixar o conceito.
 *
 * Não tem handles — não conecta com nada. Só visual.
 *
 * Estados:
 *  - inactive: borda cinza tracejada, etiqueta esmaecida
 *  - active:   borda colorida + glow, etiqueta destacada (quando o passo atual
 *              é agent_executing_tool ou agent_received_tool_result do
 *              retrieve_kb, OU agent_sending_tool_result_to_llm/
 *              agent_received_text_from_llm enquanto o último tool result foi
 *              retrieve_kb — mas pra simplicidade ativamos só nos 2 primeiros).
 */

import type { NodeProps } from "@xyflow/react";

export type RagBadgeNodeData = {
  active: boolean;
  width: number;
  height: number;
};

const COLOR_ACTIVE = "#d97706"; // amber-600 (mesma cor do ChromaDB pra coesão)
const COLOR_IDLE = "#a1a1aa"; // zinc-400

export function RagBadgeNode({ data }: NodeProps) {
  const { active, width, height } = data as RagBadgeNodeData;
  const color = active ? COLOR_ACTIVE : COLOR_IDLE;

  return (
    <div
      style={{
        width,
        height,
        border: `2px dashed ${color}`,
        borderRadius: 14,
        background: active ? `${COLOR_ACTIVE}0a` : "transparent",
        boxShadow: active ? `0 0 0 4px ${COLOR_ACTIVE}1a` : "none",
        transition: "all 200ms ease",
        position: "relative",
        pointerEvents: "none",
      }}
    >
      {/* Etiqueta — tab no topo da caixa, ligeiramente sobreposta à borda */}
      <div
        style={{
          position: "absolute",
          top: -12,
          left: 16,
          background: "#fff",
          padding: "1px 10px",
          borderRadius: 6,
          border: `1.5px solid ${color}`,
          fontSize: 12,
          fontWeight: 600,
          color,
          letterSpacing: 0.2,
          whiteSpace: "nowrap",
          transition: "all 200ms ease",
        }}
      >
        🧠 RAG (Retrieval Augmented Generation)
      </div>
    </div>
  );
}
