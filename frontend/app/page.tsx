import { AgentConsole } from "@/components/agent-console";
import { EmailSidebar } from "@/components/email-sidebar";
import { RecruiterDashboard } from "@/components/recruiter-dashboard";

export default function Home() {
  return (
    <div className="flex min-h-screen bg-[#0d1117] text-[#e6edf3]">
      <EmailSidebar />
      <div className="flex min-w-0 flex-1 flex-col xl:flex-row">
        <AgentConsole />
        <RecruiterDashboard />
      </div>
    </div>
  );
}
