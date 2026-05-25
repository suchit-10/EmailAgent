"use client";

import { useEffect, useState, type ReactNode } from "react";
import { BriefcaseBusiness, CalendarClock, CheckCircle2, Clock3, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { getDashboard, type DashboardOverview } from "@/lib/api";

export function RecruiterDashboard() {
  const [dashboard, setDashboard] = useState<DashboardOverview>({ unread: 0, urgent: 0, recruiters: 0, leads: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("Waiting for synced recruiter emails.");

  async function loadDashboard() {
    setIsLoading(true);
    try {
      const overview = await getDashboard();
      setDashboard(overview);
      setStatus(overview.leads.length ? "" : "No recruiter leads yet.");
    } catch {
      setStatus("Backend or session unavailable.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  return (
    <section className="border-t border-[#30363d] bg-[#0d1117] p-4 xl:w-[360px] xl:border-l xl:border-t-0">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BriefcaseBusiness className="h-5 w-5 text-[#3fb950]" />
          <h2 className="text-sm font-semibold">Recruiter Tracker</h2>
        </div>
        <Button size="icon" variant="ghost" onClick={loadDashboard} disabled={isLoading} title="Refresh dashboard">
          <RefreshCw className={isLoading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />
        </Button>
      </div>
      <div className="grid grid-cols-3 gap-2 xl:grid-cols-1">
        <Metric icon={<Clock3 className="h-4 w-4" />} label="Unread" value={String(dashboard.unread)} />
        <Metric icon={<CalendarClock className="h-4 w-4" />} label="Urgent" value={String(dashboard.urgent)} />
        <Metric icon={<CheckCircle2 className="h-4 w-4" />} label="Leads" value={String(dashboard.recruiters)} />
      </div>
      <div className="mt-5 space-y-2">
        {dashboard.leads.length === 0 && <div className="text-sm leading-6 text-[#8b949e]">{status}</div>}
        {dashboard.leads.map((lead, index) => (
          <motion.div
            key={`${lead.company}-${lead.role}-${lead.interview_at ?? "tracked"}-${index}`}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="rounded-md border border-[#30363d] bg-[#151b23] p-3"
          >
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium">{lead.company}</span>
              <span className="text-xs text-[#8b949e]">
                {lead.interview_at ? new Date(lead.interview_at).toLocaleDateString() : "Tracked"}
              </span>
            </div>
            <div className="mt-1 text-sm text-[#8b949e]">{lead.role}</div>
            <div className="mt-3 text-xs text-[#3fb950]">{lead.status}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#30363d] bg-[#151b23] p-3">
      <div className="flex items-center gap-2 text-[#8b949e]">{icon}<span className="text-xs">{label}</span></div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}
