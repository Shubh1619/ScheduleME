"use client";

import Link from "next/link";
import { use, useState } from "react";

import { apiFetch } from "@/lib/api";
import { useApiData } from "@/lib/useApiData";
import { useAuth } from "@/lib/auth";
import type { CampaignWithStats } from "@/lib/types";
import { Badge, Button, Card, Spinner, formatDate } from "@/components/ui";

export default function CampaignDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const campaignId = Number(id);
  const { token, activeBusiness } = useAuth();
  const businessId = activeBusiness?.id;
  const [sending, setSending] = useState(false);
  const [sendMessage, setSendMessage] = useState<string | null>(null);

  const campaign = useApiData<CampaignWithStats>(
    () =>
      apiFetch<CampaignWithStats>(`/api/v1/businesses/${businessId}/campaigns/${campaignId}`, {
        token: token ?? undefined,
      }),
    [businessId, campaignId, token]
  );

  async function handleSend() {
    if (!businessId || !token) return;
    setSending(true);
    setSendMessage(null);
    try {
      const res = await apiFetch<{ message: string }>(
        `/api/v1/businesses/${businessId}/campaigns/${campaignId}/send`,
        { method: "POST", token }
      );
      setSendMessage(res.message);
      campaign.reload();
    } catch (err) {
      setSendMessage(err instanceof Error ? err.message : "Send failed");
    } finally {
      setSending(false);
    }
  }

  if (campaign.loading) {
    return <Spinner />;
  }

  if (!campaign.data) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-slate-500">Campaign not found.</p>
        <Link href="/dashboard/campaigns" className="text-sm text-emerald-600 hover:underline">
          Back to campaigns
        </Link>
      </div>
    );
  }

  const c = campaign.data;

  const stats: { label: string; value: number; tone: "green" | "red" | "amber" | "slate" | "blue" }[] = [
    { label: "Total", value: c.stats.total, tone: "slate" },
    { label: "Queued", value: c.stats.queued, tone: "blue" },
    { label: "Sent", value: c.stats.sent, tone: "amber" },
    { label: "Delivered", value: c.stats.delivered, tone: "green" },
    { label: "Read", value: c.stats.read, tone: "green" },
    { label: "Failed", value: c.stats.failed, tone: "red" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <Link href="/dashboard/campaigns" className="text-sm text-emerald-600 hover:underline">
          Back to campaigns
        </Link>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">{c.title}</h1>
          <div className="mt-1 flex items-center gap-2 text-sm text-slate-500">
            <Badge tone={c.status === "draft" ? "slate" : c.status === "sending" ? "amber" : "green"}>
              {c.status}
            </Badge>
            <span>Created {formatDate(c.created_at)}</span>
          </div>
        </div>
        {c.status === "draft" && (
          <Button onClick={handleSend} disabled={sending}>
            {sending ? "Sending..." : "Send campaign"}
          </Button>
        )}
      </div>

      {sendMessage && (
        <div className="rounded-md bg-slate-50 px-4 py-2 text-sm text-slate-700">{sendMessage}</div>
      )}

      <Card title="Delivery">
        <div className="grid grid-cols-3 gap-4 sm:grid-cols-6">
          {stats.map((s) => (
            <div key={s.label}>
              <div className="text-2xl font-bold text-slate-900">{s.value}</div>
              <div className="text-xs uppercase tracking-wide text-slate-400">{s.label}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Message">
        <pre className="whitespace-pre-wrap rounded-md bg-slate-50 p-4 text-sm text-slate-700">{c.message_body}</pre>
      </Card>
    </div>
  );
}