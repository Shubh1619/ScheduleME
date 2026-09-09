"use client";

import { FormEvent, useState } from "react";

import { apiFetch } from "@/lib/api";
import { useApiData } from "@/lib/useApiData";
import { useAuth } from "@/lib/auth";
import type { Template } from "@/lib/types";
import { Badge, Button, Card, Input, Label, Spinner, Textarea } from "@/components/ui";

export default function TemplatesPage() {
  const { token, activeBusiness } = useAuth();
  const businessId = activeBusiness?.id;
  const [templateName, setTemplateName] = useState("");
  const [templateBody, setTemplateBody] = useState("");
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

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
      await apiFetch(`/api/v1/businesses/${businessId}/templates`, {
        method: "POST",
        token,
        body: JSON.stringify({ template_name: templateName, template_body: templateBody }),
      });
      setTemplateName("");
      setTemplateBody("");
      templates.reload();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to create template");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id: number) {
    if (!businessId || !token) return;
    try {
      await apiFetch(`/api/v1/businesses/${businessId}/templates/${id}`, {
        method: "DELETE",
        token,
      });
      templates.reload();
    } catch {
      // ignore
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-slate-900">Templates</h1>

      <Card title="Create template">
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && (
            <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>
          )}
          <div>
            <Label>Template name</Label>
            <Input
              required
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              placeholder="diwali_offer"
            />
          </div>
          <div>
            <Label>Template body</Label>
            <Textarea
              required
              rows={3}
              value={templateBody}
              onChange={(e) => setTemplateBody(e.target.value)}
              placeholder="Hello {{name}}, our Diwali special is here..."
            />
          </div>
          <Button type="submit" disabled={creating}>
            {creating ? "Creating..." : "Create template"}
          </Button>
        </form>
      </Card>

      {templates.loading ? (
        <Spinner />
      ) : templates.data && templates.data.length > 0 ? (
        <Card>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-400">
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Body</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {templates.data.map((t) => (
                <tr key={t.id} className="border-b border-slate-100 last:border-0">
                  <td className="py-2 pr-4 font-medium text-slate-800">{t.template_name}</td>
                  <td className="py-2 pr-4 max-w-[300px] truncate text-slate-500">{t.template_body}</td>
                  <td className="py-2 pr-4">
                    <Badge tone="slate">{t.status}</Badge>
                  </td>
                  <td className="py-2 text-right">
                    <button onClick={() => handleDelete(t.id)} className="text-xs font-medium text-red-600 hover:underline">
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
          <p className="text-sm text-slate-500">No templates yet. Create one above.</p>
        </Card>
      )}
    </div>
  );
}