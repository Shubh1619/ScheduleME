"use client";

import Link from "next/link";

import { apiFetch } from "@/lib/api";
import { useApiData } from "@/lib/useApiData";
import { useAuth } from "@/lib/auth";
import type { Campaign, Contact, WhatsAppAccount } from "@/lib/types";
import { Badge, Card, Spinner, formatDate } from "@/components/ui";

function statusTone(status: string): "green" | "red" | "amber" | "slate" | "blue" {
  switch (status) {
    case "draft":
      return "slate";
    case "sending":
      return "amber";
    case "completed":
      return "green";
    case "failed":
      return "red";
    default:
      return "slate";
  }
}

export default function OverviewPage() {
  const { token, activeBusiness } = useAuth();
  const businessId = activeBusiness?.id;

  const account = useApiData<WhatsAppAccount | null>(
    () =>
      apiFetch<WhatsAppAccount>(`/api/v1/whatsapp/account?business_id=${businessId}`, {
        token: token ?? undefined,
      }).catch((err) => {
        if (err.status === 404) return null;
        throw err;
      }),
    [businessId, token]
  );

  const campaigns = useApiData<Campaign[]>(
    () =>
      apiFetch<Campaign[]>(`/api/v1/businesses/${businessId}/campaigns?limit=5`, {
        token: token ?? undefined,
      }),
    [businessId, token]
  );

  const contacts = useApiData<Contact[]>(
    () =>
      apiFetch<Contact[]>(`/api/v1/businesses/${businessId}/contacts?limit=5`, {
        token: token ?? undefined,
      }),
    [businessId, token]
  );

  if (!businessId) {
    return <p className="text-sm text-slate-500">No business found. Create one from registration.</p>;
  }

  const connected = account.data !== null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">
          Welcome back, {activeBusiness?.business_name}
        </h1>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="WhatsApp Number">
          {account.loading ? (
            <Spinner />
          ) : connected && account.data ? (
            <div className="space-y-2">
              <Badge tone="green">{account.data.phone_number}</Badge>
              <p className="text-sm text-slate-600">{account.data.display_name}</p>
            </div>
          ) : (
            <div className="space-y-2">
              <Badge tone="red">Not connected</Badge>
              <p className="text-sm text-slate-500">
                Connect your WhatsApp Business number to start sending.{" "}
                <Link href="/dashboard/whatsapp" className="text-emerald-600">
                  Connect here
                </Link>
              </p>
            </div>
          )}
        </Card>

        <Card title="Recent Campaigns">
          {campaigns.loading ? (
            <Spinner />
          ) : campaigns.data && campaigns.data.length > 0 ? (
            <ul className="space-y-2">
              {campaigns.data.map((c) => (
                <li key={c.id} className="flex items-center justify-between text-sm">
                  <span className="truncate text-slate-700">{c.title}</span>
                  <Badge tone={statusTone(c.status)}>{c.status}</Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">
              No campaigns yet.{" "}
              <Link href="/dashboard/campaigns" className="text-emerald-600">
                Create one
              </Link>
            </p>
          )}
        </Card>

        <Card title="Recent Contacts">
          {contacts.loading ? (
            <Spinner />
          ) : contacts.data && contacts.data.length > 0 ? (
            <ul className="space-y-2">
              {contacts.data.map((ct) => (
                <li key={ct.id} className="flex items-center justify-between text-sm">
                  <span className="truncate text-slate-700">{ct.name}</span>
                  <span className="text-xs text-slate-400">{ct.phone}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">
              No contacts yet.{" "}
              <Link href="/dashboard/contacts" className="text-emerald-600">
                Add some
              </Link>
            </p>
          )}
        </Card>
      </div>

      <Card title="Campaign Timeline">
        {campaigns.data && campaigns.data.length > 0 ? (
          <ul className="space-y-2">
            {campaigns.data.map((c) => (
              <li key={c.id} className="flex items-center justify-between text-sm">
                <span className="text-slate-700">{c.title}</span>
                <span className="text-xs text-slate-400">{formatDate(c.created_at)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">Nothing scheduled yet.</p>
        )}
      </Card>
    </div>
  );
}