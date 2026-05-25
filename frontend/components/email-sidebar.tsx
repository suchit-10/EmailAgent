"use client";

import { useEffect, useMemo, useState } from "react";
import { Inbox, RefreshCw, Search, Tag, Timer, TriangleAlert } from "lucide-react";
import { motion } from "framer-motion";
import type { EmailItem } from "@/types/email";
import { searchEmails, syncEmails } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function EmailSidebar() {
  const [query, setQuery] = useState("recruiter OR interview OR assessment");
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [status, setStatus] = useState("Connect Gmail, then sync your inbox.");
  const [isLoading, setIsLoading] = useState(false);

  const emptyCopy = useMemo(() => (isLoading ? "Loading inbox..." : status), [isLoading, status]);

  async function loadEmails(nextQuery = query) {
    setIsLoading(true);
    try {
      const items = await searchEmails(nextQuery);
      setEmails(
        items.map((email) => ({
          id: email.id,
          sender: email.from,
          subject: email.subject,
          snippet: email.snippet,
          classification: email.classification,
          urgency: email.urgency,
          receivedAt: email.received_at ? new Date(email.received_at).toLocaleDateString() : "Synced"
        }))
      );
      setStatus(items.length ? "" : "No matching emails found.");
    } catch {
      setStatus("Start the backend and connect Gmail to load real inbox data.");
    } finally {
      setIsLoading(false);
    }
  }

  async function syncAndLoad() {
    setIsLoading(true);
    try {
      const count = await syncEmails();
      setStatus(`Synced ${count} recent emails.`);
      await loadEmails();
    } catch {
      setStatus("Could not sync Gmail. Check your Google connection.");
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadEmails();
  }, []);

  return (
    <aside className="hidden w-[340px] shrink-0 border-r border-[#30363d] bg-[#111820] lg:block">
      <div className="flex h-14 items-center justify-between gap-2 border-b border-[#30363d] px-4">
        <div className="flex items-center gap-2">
          <Inbox className="h-5 w-5 text-[#2f81f7]" />
          <span className="font-semibold">Inbox Intelligence</span>
        </div>
        <Button size="icon" variant="ghost" onClick={syncAndLoad} disabled={isLoading} title="Sync Gmail">
          <RefreshCw className={isLoading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
        </Button>
      </div>
      <div className="border-b border-[#30363d] p-3">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            loadEmails();
          }}
          className="flex h-10 items-center gap-2 rounded-md border border-[#30363d] bg-[#0d1117] px-3 text-sm text-[#8b949e]"
        >
          <Search className="h-4 w-4" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="min-w-0 flex-1 bg-transparent text-[#e6edf3] outline-none placeholder:text-[#6e7681]"
            placeholder="recruiter, OA, urgent, Amazon"
          />
        </form>
      </div>
      <div className="thin-scrollbar h-[calc(100vh-7rem)] overflow-y-auto">
        {emails.length === 0 && <div className="px-4 py-5 text-sm leading-6 text-[#8b949e]">{emptyCopy}</div>}
        {emails.map((email, index) => (
          <motion.button
            key={email.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.04 }}
            className="block w-full border-b border-[#21262d] px-4 py-4 text-left hover:bg-[#1f2937]"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="truncate text-sm font-medium">{email.sender}</span>
              <span className="shrink-0 text-xs text-[#8b949e]">{email.receivedAt}</span>
            </div>
            <div className="mt-2 line-clamp-1 text-sm font-semibold">{email.subject}</div>
            <p className="mt-1 line-clamp-2 text-sm leading-5 text-[#8b949e]">{email.snippet}</p>
            <div className="mt-3 flex items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1 rounded-sm bg-[#1f6feb26] px-2 py-1 text-[#79c0ff]">
                <Tag className="h-3 w-3" />
                {email.classification}
              </span>
              {email.urgency > 75 ? (
                <span className="inline-flex items-center gap-1 rounded-sm bg-[#d2992226] px-2 py-1 text-[#e3b341]">
                  <TriangleAlert className="h-3 w-3" />
                  urgent
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-sm bg-[#30363d] px-2 py-1 text-[#8b949e]">
                  <Timer className="h-3 w-3" />
                  low
                </span>
              )}
            </div>
          </motion.button>
        ))}
      </div>
    </aside>
  );
}
