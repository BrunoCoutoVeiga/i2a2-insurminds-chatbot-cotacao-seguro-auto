"use client";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div
      className={cn(
        "flex w-full items-start gap-3",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-lg">
          🚗
        </div>
      )}
      <Card
        className={cn(
          "max-w-[80%] px-4 py-3 shadow-sm",
          isUser
            ? "bg-blue-600 text-white border-blue-700"
            : "bg-white border-zinc-200",
        )}
      >
        <div
          className={cn(
            "prose prose-sm max-w-none break-words",
            isUser
              ? "prose-invert prose-headings:text-white prose-strong:text-white"
              : "prose-zinc",
          )}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </Card>
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-200 text-sm font-medium text-zinc-700">
          Eu
        </div>
      )}
    </div>
  );
}
