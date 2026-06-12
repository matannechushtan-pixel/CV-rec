"use client";

import { useEffect, useRef, useState } from "react";
import api from "@/lib/api";
import type { CV } from "@/lib/types";
import { Compass, Send, Plus, FileText } from "lucide-react";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const STARTER_QUESTIONS = [
  "What career paths fit my background?",
  "How can I improve my CV for tech roles?",
  "How should I prepare for a salary negotiation?",
  "What skills should I develop in the next 6 months?",
];

function renderMarkdown(text: string) {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];

  function flushList() {
    if (listItems.length === 0) return;
    elements.push(
      <ul key={`ul-${elements.length}`} className="list-disc space-y-1 pl-5">
        {listItems.map((item, i) => (
          <li key={i}>{renderInline(item)}</li>
        ))}
      </ul>
    );
    listItems = [];
  }

  function renderInline(line: string): React.ReactNode {
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  }

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      listItems.push(trimmed.slice(2));
      continue;
    }
    flushList();
    if (trimmed === "") {
      elements.push(<div key={`sp-${elements.length}`} className="h-2" />);
    } else if (trimmed.startsWith("### ")) {
      elements.push(
        <h4 key={`h-${elements.length}`} className="text-sm font-semibold text-white">
          {renderInline(trimmed.slice(4))}
        </h4>
      );
    } else if (trimmed.startsWith("## ")) {
      elements.push(
        <h3 key={`h-${elements.length}`} className="text-base font-semibold text-white">
          {renderInline(trimmed.slice(3))}
        </h3>
      );
    } else {
      elements.push(<p key={`p-${elements.length}`}>{renderInline(line)}</p>);
    }
  }
  flushList();
  return elements;
}

export default function CareerChatPage() {
  const [cvs, setCvs] = useState<CV[]>([]);
  const [selectedCvId, setSelectedCvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .get<CV[]>("/cv/")
      .then(({ data }) => {
        setCvs(data);
        const active = data.find((c) => c.is_base) ?? data[0];
        if (active) setSelectedCvId(active.id);
      })
      .catch(() => {});
  }, []);

  function storageKey(cvId: string | null) {
    return `career-chat-messages-${cvId ?? "none"}`;
  }

  useEffect(() => {
    try {
      const stored = localStorage.getItem(storageKey(selectedCvId));
      setMessages(stored ? (JSON.parse(stored) as ChatMessage[]) : []);
    } catch {
      setMessages([]);
    }
  }, [selectedCvId]);

  useEffect(() => {
    try {
      localStorage.setItem(storageKey(selectedCvId), JSON.stringify(messages));
    } catch {
      // ignore storage errors
    }
  }, [messages, selectedCvId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  function newConversation() {
    setMessages([]);
    setError(null);
  }

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || streaming) return;

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: trimmed }];
    setMessages([...nextMessages, { role: "assistant", content: "" }]);
    setInput("");
    setError(null);
    setStreaming(true);

    try {
      const baseURL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

      const res = await fetch(`${baseURL}/career-chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          messages: nextMessages,
          cv_id: selectedCvId ?? undefined,
        }),
      });

      if (!res.ok || !res.body) {
        throw new Error("Request failed");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let assistantText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const event of events) {
          const line = event.trim();
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6);
          if (payload === "[DONE]") continue;
          try {
            const parsed = JSON.parse(payload) as { text: string };
            assistantText += parsed.text;
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = { role: "assistant", content: assistantText };
              return updated;
            });
          } catch {
            // ignore malformed chunks
          }
        }
      }
    } catch {
      setError("Failed to reach the career coach. Please try again.");
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setStreaming(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      <aside className="hidden w-64 flex-shrink-0 flex-col gap-4 lg:flex">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Career Coach</h1>
          <p className="mt-1 text-xs text-slate-400">
            Chat with an AI career coach for personalized guidance.
          </p>
        </div>

        <button type="button" onClick={newConversation} className="btn-secondary w-full justify-center">
          <Plus className="h-3.5 w-3.5" />
          Clear conversation
        </button>

        {cvs.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              CV context
            </p>
            <div className="space-y-1">
              {cvs.map((cv) => (
                <button
                  key={cv.id}
                  type="button"
                  onClick={() => setSelectedCvId(cv.id)}
                  className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs transition-colors ${
                    selectedCvId === cv.id
                      ? "bg-blue-500/20 text-blue-300"
                      : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                  }`}
                >
                  <FileText className="h-3.5 w-3.5 flex-shrink-0" />
                  <span className="truncate">{cv.version_name ?? "Untitled CV"}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Try asking
          </p>
          <div className="space-y-1">
            {STARTER_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => sendMessage(q)}
                disabled={streaming}
                className="block w-full rounded-lg px-2.5 py-1.5 text-left text-xs text-slate-400 transition-colors hover:bg-white/5 hover:text-slate-200"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </aside>

      <div className="flex flex-1 flex-col rounded-2xl border border-white/10 bg-white/5">
        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-slate-400">
              <Compass className="h-10 w-10 text-blue-400" />
              <p className="text-sm">
                Ask about career planning, job search strategy, interview prep, or your CV.
              </p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                  m.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-white/10 text-slate-100"
                }`}
              >
                {m.role === "assistant" && m.content === "" && streaming ? (
                  <span className="text-slate-400">Thinking…</span>
                ) : m.role === "assistant" ? (
                  <div className="space-y-1">{renderMarkdown(m.content)}</div>
                ) : (
                  <p className="whitespace-pre-wrap">{m.content}</p>
                )}
              </div>
            </div>
          ))}
        </div>

        {error && <p className="px-4 pb-2 text-sm text-red-400">{error}</p>}

        <div className="border-t border-white/10 p-3">
          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder="Ask your career coach…"
              className="max-h-40 flex-1 resize-none rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/30"
            />
            <button
              type="button"
              onClick={() => sendMessage(input)}
              disabled={streaming || !input.trim()}
              className="btn-primary !px-3 !py-2"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
