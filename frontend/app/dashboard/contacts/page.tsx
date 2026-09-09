"use client";

import { FormEvent, useRef, useState } from "react";

import { apiFetch } from "@/lib/api";
import { useApiData } from "@/lib/useApiData";
import { useAuth } from "@/lib/auth";
import type { Contact } from "@/lib/types";
import { Badge, Button, Card, Input, Label, Spinner } from "@/components/ui";

interface BulkResult {
  created: number;
  skipped: number;
  errors: string[];
}

export default function ContactsPage() {
  const { token, activeBusiness } = useAuth();
  const businessId = activeBusiness?.id;
  const fileRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [attributes, setAttributes] = useState("");
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<BulkResult | null>(null);

  const contacts = useApiData<Contact[]>(
    () =>
      apiFetch<Contact[]>(`/api/v1/businesses/${businessId}/contacts`, {
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
      const parsed: Record<string, unknown> = {};
      if (attributes.trim()) {
        Object.assign(parsed, JSON.parse(attributes));
      }
      await apiFetch(`/api/v1/businesses/${businessId}/contacts`, {
        method: "POST",
        token,
        body: JSON.stringify({ name, phone, attributes: parsed }),
      });
      setName("");
      setPhone("");
      setAttributes("");
      contacts.reload();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to add contact");
    } finally {
      setCreating(false);
    }
  }

  async function handleUpload() {
    if (!businessId || !token || !uploadFile) return;
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const form = new FormData();
      form.append("file", uploadFile);
      const result = await apiFetch<BulkResult>(
        `/api/v1/businesses/${businessId}/contacts/upload`,
        { method: "POST", token, body: form }
      );
      setUploadResult(result);
      setUploadFile(null);
      if (fileRef.current) fileRef.current.value = "";
      contacts.reload();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleToggleOptIn(contact: Contact) {
    if (!businessId || !token) return;
    try {
      await apiFetch(`/api/v1/businesses/${businessId}/contacts/${contact.id}`, {
        method: "PATCH",
        token,
        body: JSON.stringify({ opted_in: !contact.opted_in }),
      });
      contacts.reload();
    } catch {
      // ignore
    }
  }

  async function handleDelete(contact: Contact) {
    if (!businessId || !token) return;
    try {
      await apiFetch(`/api/v1/businesses/${businessId}/contacts/${contact.id}`, {
        method: "DELETE",
        token,
      });
      contacts.reload();
    } catch {
      // ignore
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-slate-900">Contacts</h1>

      <Card title="Add contact">
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && (
            <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>
          )}
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <Label>Name</Label>
              <Input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Alice" />
            </div>
            <div>
              <Label>Phone (with country code)</Label>
              <Input required value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91 98765 43210" />
            </div>
            <div>
              <Label>Attributes (JSON, optional)</Label>
              <Input
                value={attributes}
                onChange={(e) => setAttributes(e.target.value)}
                placeholder={`{"city": "Mumbai"}`}
              />
            </div>
          </div>
          <Button type="submit" disabled={creating}>
            {creating ? "Adding..." : "Add contact"}
          </Button>
        </form>
      </Card>

      <Card title="Upload contacts (CSV)">
        <div className="space-y-3">
          <p className="text-sm text-slate-500">Columns: <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">name</code>, <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">phone</code> required; <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">opted_in</code>, <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">attributes</code> optional.</p>
          <div className="flex items-center gap-3">
            <input
              ref={fileRef}
              type="file"
              accept=".csv,text/csv"
              className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200"
              onChange={(e) => {
                setUploadFile(e.target.files?.[0] ?? null);
                setUploadError(null);
                setUploadResult(null);
              }}
            />
            <Button type="button" onClick={handleUpload} disabled={uploading || !uploadFile}>
              {uploading ? "Uploading..." : "Upload"}
            </Button>
          </div>
          {uploadError && (
            <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{uploadError}</div>
          )}
          {uploadResult && (
            <div className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
              {uploadResult.created} created, {uploadResult.skipped} skipped
              {uploadResult.errors.length > 0 && (
                <ul className="mt-1 list-inside list-disc text-red-700">
                  {uploadResult.errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </Card>

      {contacts.loading ? (
        <Spinner />
      ) : contacts.data && contacts.data.length > 0 ? (
        <Card>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-400">
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Phone</th>
                <th className="py-2 pr-4">Opt-in</th>
                <th className="py-2 pr-4">Attributes</th>
                <th className="py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {contacts.data.map((contact) => (
                <tr key={contact.id} className="border-b border-slate-100 last:border-0">
                  <td className="py-2 pr-4 font-medium text-slate-800">{contact.name}</td>
                  <td className="py-2 pr-4 text-slate-600">{contact.phone}</td>
                  <td className="py-2 pr-4">
                    <button onClick={() => handleToggleOptIn(contact)}>
                      {contact.opted_in ? <Badge tone="green">opted in</Badge> : <Badge tone="red">opted out</Badge>}
                    </button>
                  </td>
                  <td className="py-2 pr-4 max-w-[200px] truncate text-xs text-slate-400">
                    {Object.keys(contact.attributes ?? {}).join(", ") || "-"}
                  </td>
                  <td className="py-2 text-right">
                    <button
                      onClick={() => handleDelete(contact)}
                      className="text-xs font-medium text-red-600 hover:text-red-700"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : (
        <Card>
          <p className="text-sm text-slate-500">No contacts yet. Add your first customer above.</p>
        </Card>
      )}
    </div>
  );
}