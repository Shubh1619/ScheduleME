"use client";

import { useState } from "react";

import { apiFetch } from "@/lib/api";
import { useApiData } from "@/lib/useApiData";
import { useAuth } from "@/lib/auth";
import type { WhatsAppAccount } from "@/lib/types";
import { Badge, Button, Card, Spinner } from "@/components/ui";

export default function WhatsAppPage() {
  const { token, activeBusiness } = useAuth();
  const businessId = activeBusiness?.id;
  const [connecting, setConnecting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [disconnecting, setDisconnecting] = useState(false);

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

  async function handleConnect() {
    if (!businessId || !token) return;
    setActionError(null);
    setConnecting(true);
    try {
      const res = await apiFetch<{ auth_url: string }>("/api/v1/whatsapp/connect", {
        method: "POST",
        token,
        body: JSON.stringify({ business_id: businessId }),
      });
      window.open(res.auth_url, "_blank", "noopener,noreferrer");
      setActionSuccess("Meta onboarding opened in a new tab. Complete it, then click Refresh Status.");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to start connection");
    } finally {
      setConnecting(false);
    }
  }

  async function handleDisconnect() {
    if (!businessId || !token) return;
    setActionError(null);
    setDisconnecting(true);
    try {
      await apiFetch<void>(`/api/v1/whatsapp/account?business_id=${businessId}`, {
        method: "DELETE",
        token,
      });
      setActionSuccess("WhatsApp disconnected.");
      account.reload();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to disconnect");
    } finally {
      setDisconnecting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">Connect WhatsApp</h1>
        {!account.loading && (
          <Button variant="secondary" onClick={account.reload}>
            Refresh Status
          </Button>
        )}
      </div>

      {actionError && (
        <div className="rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">{actionError}</div>
      )}
      {actionSuccess && (
        <div className="rounded-md bg-emerald-50 px-4 py-2 text-sm text-emerald-700">{actionSuccess}</div>
      )}

      {!businessId ? (
        <p className="text-sm text-slate-500">No business found.</p>
      ) : account.loading ? (
        <Spinner />
      ) : account.data ? (
        <Card title="Connected">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Badge tone="green">Connected</Badge>
              <span className="text-sm text-slate-500">{account.data.status}</span>
            </div>
            <div className="text-2xl font-semibold text-slate-900">{account.data.phone_number}</div>
            <div className="text-sm text-slate-600">{account.data.display_name}</div>
            <dl className="grid grid-cols-2 gap-4 pt-2 text-sm">
              <div>
                <dt className="text-slate-400">WABA ID</dt>
                <dd className="font-mono text-slate-700">{account.data.waba_id}</dd>
              </div>
              <div>
                <dt className="text-slate-400">Phone Number ID</dt>
                <dd className="font-mono text-slate-700">{account.data.phone_number_id}</dd>
              </div>
            </dl>
            <Button variant="danger" onClick={handleDisconnect} disabled={disconnecting}>
              {disconnecting ? "Disconnecting..." : "Disconnect"}
            </Button>
          </div>
        </Card>
      ) : (
        <Card title="Not connected">
          <div className="space-y-4">
            <div>
              <Badge tone="red">Not connected</Badge>
            </div>
            <p className="text-sm text-slate-600">
              Connect your own WhatsApp Business number. Your customers will see your business
              name and number as the sender.
            </p>
            <ol className="list-inside list-decimal space-y-1 text-sm text-slate-600">
              <li>Click Connect WhatsApp below.</li>
              <li>Complete Meta&apos;s business onboarding (own WABA + phone number).</li>
              <li>Return here and click Refresh Status.</li>
            </ol>
            <Button onClick={handleConnect} disabled={connecting}>
              {connecting ? "Opening Meta..." : "Connect WhatsApp"}
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}