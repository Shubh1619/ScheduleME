export type User = {
  id: number;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
};

export type Business = {
  id: number;
  user_id: number;
  business_name: string;
  created_at: string;
  updated_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type WhatsAppAccount = {
  id: number;
  business_id: number;
  waba_id: string;
  phone_number_id: string;
  phone_number: string;
  display_name: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Contact = {
  id: number;
  business_id: number;
  name: string;
  phone: string;
  attributes: Record<string, string> | Record<string, unknown>;
  opted_in: boolean;
  created_at: string;
  updated_at: string;
};

export type Campaign = {
  id: number;
  business_id: number;
  template_id: number | null;
  title: string;
  status: string;
  message_body: string;
  scheduled_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CampaignStats = {
  total: number;
  queued: number;
  sent: number;
  delivered: number;
  read: number;
  failed: number;
};

export type CampaignWithStats = Campaign & { stats: CampaignStats };

export type Template = {
  id: number;
  business_id: number;
  template_name: string;
  template_body: string;
  language: string;
  category: string;
  status: string;
  created_at: string;
  updated_at: string;
};