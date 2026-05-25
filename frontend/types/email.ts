export type EmailItem = {
  id: string;
  sender: string;
  subject: string;
  snippet: string;
  classification: string;
  urgency: number;
  receivedAt: string;
};

export type RecruiterLead = {
  company: string;
  role: string;
  status: string;
  interview_at?: string | null;
};
