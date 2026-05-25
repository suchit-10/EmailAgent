"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, CalendarPlus, Check, FileText, MailPlus, Send, Sparkles, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { approveDraft, getAuthStatus, googleLoginUrl, invokeAgent, type AuthStatus } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
  draft?: { id: string; subject: string; body: string; status: string };
};

const prompts = [
  { icon: <Sparkles className="h-4 w-4" />, text: "Summarize important unread emails" },
  { icon: <MailPlus className="h-4 w-4" />, text: "Reply professionally to the latest recruiter email" },
  { icon: <CalendarPlus className="h-4 w-4" />, text: "Find interview emails and add them to calendar" },
  { icon: <FileText className="h-4 w-4" />, text: "Find emails mentioning OA or coding test" }
];

export function AgentConsole() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "I can search, summarize, classify, draft, and coordinate Gmail workflows. Sending always waits for your approval."
    }
  ]);
  const [input, setInput] = useState("");
  const [draftRecipients, setDraftRecipients] = useState<Record<string, string>>({});
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const canSend = useMemo(() => input.trim().length > 0 && !isLoading, [input, isLoading]);

  useEffect(() => {
    getAuthStatus().then(setAuthStatus);
    function refreshAuthStatus() {
      getAuthStatus().then(setAuthStatus);
    }
    window.addEventListener("email-sync-complete", refreshAuthStatus);
    return () => window.removeEventListener("email-sync-complete", refreshAuthStatus);
  }, []);

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    if (!canSend) return;
    const content = input.trim();
    setInput("");
    setMessages((current) => [...current, { role: "user", content }]);
    setIsLoading(true);
    try {
      const result = await invokeAgent(content);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: result.response ?? "Workflow completed.", draft: result.draft }
      ]);
    } catch {
      setMessages((current) => [
        ...current,
        { role: "assistant", content: "I could not reach the backend. Connect Google and start the FastAPI service, then try again." }
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  async function createGmailDraft(message: Message) {
    if (!message.draft) return;
    const recipients = (draftRecipients[message.draft.id] ?? "")
      .split(",")
      .map((recipient) => recipient.trim())
      .filter(Boolean);
    if (recipients.length === 0) {
      setMessages((current) => [...current, { role: "assistant", content: "Add at least one recipient before creating the Gmail draft." }]);
      return;
    }
    try {
      await approveDraft({ to: recipients, subject: message.draft.subject, body: message.draft.body });
      setMessages((current) => [...current, { role: "assistant", content: "Gmail draft created for review." }]);
    } catch {
      setMessages((current) => [...current, { role: "assistant", content: "I could not create the Gmail draft. Add recipients and confirm Google is connected." }]);
    }
  }

  return (
    <main className="flex min-w-0 flex-1 flex-col">
      <header className="flex h-14 items-center justify-between border-b border-[#30363d] px-4">
        <div>
          <h1 className="text-base font-semibold">AI Email Agent</h1>
          <p className="text-xs text-[#8b949e]">Gmail reasoning, memory, tools, and autonomous workflows</p>
        </div>
        <div className="flex items-center gap-2">
          {authStatus?.google_connected && (
            <span className="hidden max-w-56 truncate text-xs text-[#8b949e] sm:inline">
              {authStatus.email} · {authStatus.synced_emails} synced
            </span>
          )}
          <a
            href={googleLoginUrl}
            className="inline-flex h-8 items-center justify-center rounded-md border border-[#30363d] bg-[#151b23] px-3 text-sm transition hover:bg-[#21262d]"
          >
            {authStatus?.google_connected ? "Reconnect Gmail" : "Connect Gmail"}
          </a>
        </div>
      </header>
      <div className="thin-scrollbar flex-1 overflow-y-auto px-4 py-5">
        <div className="mx-auto max-w-3xl space-y-4">
          <div className="grid gap-2 sm:grid-cols-2">
            {prompts.map((prompt) => (
              <button
                key={prompt.text}
                onClick={() => setInput(prompt.text)}
                className="flex min-h-12 items-center gap-2 rounded-md border border-[#30363d] bg-[#151b23] px-3 py-2 text-left text-sm hover:bg-[#1f2937]"
              >
                <span className="text-[#79c0ff]">{prompt.icon}</span>
                <span>{prompt.text}</span>
              </button>
            ))}
          </div>
          <AnimatePresence initial={false}>
            {messages.map((message, index) => (
              <motion.div
                key={`${message.role}-${index}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={message.role === "user" ? "flex justify-end" : "flex justify-start"}
              >
                <div className="flex max-w-[86%] gap-3 rounded-md border border-[#30363d] bg-[#151b23] p-3">
                  <div className="mt-0.5 shrink-0 text-[#8b949e]">
                    {message.role === "user" ? <UserRound className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>
                  <div className="min-w-0">
                    <p className="whitespace-pre-wrap text-sm leading-6 text-[#e6edf3]">{message.content}</p>
                    {message.draft && (
                      <div className="mt-3 rounded-md border border-[#30363d] bg-[#0d1117] p-3">
                        <div className="text-xs uppercase text-[#8b949e]">Pending draft</div>
                        <div className="mt-1 text-sm font-semibold">{message.draft.subject}</div>
                        <p className="mt-2 max-h-40 overflow-y-auto whitespace-pre-wrap text-sm leading-6 text-[#c9d1d9]">
                          {message.draft.body}
                        </p>
                        <input
                          value={draftRecipients[message.draft.id] ?? ""}
                          onChange={(event) =>
                            setDraftRecipients((current) => ({ ...current, [message.draft!.id]: event.target.value }))
                          }
                          className="mt-3 h-9 w-full rounded-md border border-[#30363d] bg-[#111820] px-3 text-sm outline-none placeholder:text-[#6e7681]"
                          placeholder="recipient@example.com"
                        />
                        <Button className="mt-3" variant="outline" size="sm" onClick={() => createGmailDraft(message)}>
                          <Check className="h-4 w-4" />
                          Create Gmail draft
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {isLoading && <div className="text-sm text-[#8b949e]">Planning workflow and selecting tools...</div>}
        </div>
      </div>
      <form onSubmit={submit} className="border-t border-[#30363d] bg-[#111820] p-4">
        <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-md border border-[#30363d] bg-[#0d1117] p-2">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask your inbox: recruiter emails, Amazon updates, follow-ups, interview scheduling..."
            rows={2}
            className="max-h-36 min-h-12 flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-[#6e7681]"
          />
          <Button type="submit" size="icon" disabled={!canSend} aria-label="Send message">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </main>
  );
}
