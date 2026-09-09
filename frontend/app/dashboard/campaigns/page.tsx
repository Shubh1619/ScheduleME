"use client";

import Link from "next/link";
import { Suspense, FormEvent, useState } from "react";
import { useSearchParams } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { useApiData } from "@/lib/useApiData";
import { useAuth } from "@/lib/auth";
import type { Campaign, CampaignWithStats, Template } from "@/lib/types";
import { Badge, Button, Card, Input, Label, Spinner, Textarea, formatDate } from "@/components/ui";

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

function CampaignDetailView({ id }: { id: number }) {
  const { token, activeBusiness } = useAuth();
  const businessId = activeBusiness?.id;
  const [sending, setSending] = useState(false);
  const [sendMessage, setSendMessage] = useState<string | null>(null);

  const campaign = useApiData<CampaignWithStats>(
    () =>
      apiFetch<CampaignWithStats>(`/api/v1/businesses/${businessId}/campaigns/${id}`, {
        token: token ?? undefined,
      }),
    [businessId, id, token]
  );

  async function handleSend() {
    if (!businessId || !token) return;
    setSending(true);
    setSendMessage(null);
    try {
      const res = await apiFetch<{ message: string }>(
        `/api/v1/businesses/${businessId}/campaigns/${id}/send`,
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

function CampaignsInner() {
  const { token, activeBusiness } = useAuth();
  const businessId = activeBusiness?.id;
  const searchParams = useSearchParams();
  const viewId = searchParams.get("view");
  const [title, setTitle] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [messageBody, setMessageBody] = useState("");
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [sendingId, setSendingId] = useState<number | null>(null);

  const campaigns = useApiData<Campaign[]>(
    () =>
      apiFetch<Campaign[]>(`/api/v1/businesses/${businessId}/campaigns`, {
        token: token ?? undefined,
      }),
    [businessId, token]
  );

  const templates = useApiData<Template[]>(
    () =>
      apiFetch<Template[]>(`/api/v1/businesses/${businessId}/templates`, {
        token: token ?? undefined,
      }),
    [businessId, token]
  );

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!businessId || !token) return;
    setFormError(null);
    setCreating(true);
    try {
      await apiFetch(`/api/v1/businesses/${businessId}/campaigns`, {
        method: "POST",
        token,
        body: JSON.stringify({
          title,
          message_body: messageBody,
          template_id: templateId ? Number(templateId) : null,
        }),
      });
      setTitle("");
      setTemplateId("");
      setMessageBody("");
      campaigns.reload();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to create campaign");
    } finally {
      setCreating(false);
    }
  }

  async function handleSend(id: number) {
    if (!businessId || !token) return;
    setSendingId(id);
    try {
      await apiFetch(`/api/v1/businesses/${businessId}/campaigns/${id}/send`, {
        method: "POST",
        token,
      });
      campaigns.reload();
    } catch {
      // ignore
    } finally {
      setSendingId(null);
    }
  }

  async function handleDelete(id: number) {
    if (!businessId || !token) return;
    try {
      await apiFetch(`/api/v1/businesses/${businessId}/campaigns/${id}`, {
        method: "DELETE",
        token,
      });
      campaigns.reload();
    } catch {
      // ignore
    }
  }

  if (viewId) {
    const numericId = Number(viewId);
    if (Number.isNaN(numericId)) {
      return (
        <Card>
          <p className="text-sm text-slate-500">Invalid campaign id.</p>
        </Card>
      );
    }
    return <CampaignDetailView id={numericId} />;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-slate-900">Campaigns</h1>

      <Card title="Create campaign">
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && (
            <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label>Campaign name</Label>
              <Input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Diwali Offer" />
            </div>
            <div>
              <Label>Template (optional)</Label>
              <select
                value={templateId}
                onChange={(e) => setTemplateId(e.target.value)}
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="">No template</option>
                {templates.data?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.template_name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <Label>Message</Label>
            <Textarea
              required
              rows={4}
              value={messageBody}
              onChange={(e) => setMessageBody(e.target.value)}
              placeholder="Hello {{name}}, our Diwali special offers are live..."
            />
            <p className="mt-1 text-xs text-slate-400">Use {"{{name}}"} and other contact attributes as placeholders.</p>
          </div>
          <Button type="submit" disabled={creating}>
            {creating ? "Creating..." : "Create campaign"}
          </Button>
        </form>
      </Card>

      {campaigns.loading ? (
        <Spinner />
      ) : campaigns.data && campaigns.data.length > 0 ? (
        <Card>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-400">
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Created</th>
                <th className="py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.data.map((c) => (
                <tr key={c.id} className="border-b border-slate-100 last:border-0">
                  <td className="py-2 pr-4">
                    <Link href={`/dashboard/campaigns?view=${c.id}`} className="font-medium text-emerald-700 hover:underline">
                      {c.title}
                    </Link>
                  </td>
                  <td className="py-2 pr-4">
                    <Badge tone={statusTone(c.status)}>{c.status}</Badge>
                  </td>
                  <td className="py-2 pr-4 text-slate-500">{new Date(c.created_at).toLocaleDateString()}</td>
                  <td className="py-2 text-right">
                    <div className="inline-flex items-center gap-3">
                      {c.status === "draft" && (
                        <button
                          onClick={() => handleSend(c.id)}
                          disabled={sendingId === c.id}
                          className="text-xs font-medium text-emerald-700 hover:underline disabled:opacity-50"
                        >
                          {sendingId === c.id ? "Sending..." : "Send"}
                        </button>
                      )}
                      <button onClick={() => handleDelete(c.id)} className="text-xs font-medium text-red-600 hover:underline">
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : (
        <Card>
          <p className="text-sm text-slate-500">No campaigns yet. Create your first one above.</p>
        </Card>
      )}
    </div>
  );
}

export default function CampaignsPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <CampaignsInner />
    </Suspense>
  );
}