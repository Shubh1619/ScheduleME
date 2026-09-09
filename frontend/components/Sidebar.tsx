"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth";
import { cn } from "@/components/ui";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/whatsapp", label: "WhatsApp" },
  { href: "/dashboard/contacts", label: "Contacts" },
  { href: "/dashboard/campaigns", label: "Campaigns" },
  { href: "/dashboard/templates", label: "Templates" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, activeBusiness, businesses, setActiveBusinessId, logout } = useAuth();

  return (
    <aside className="flex w-60 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-5 py-4">
        <div className="text-sm font-bold text-slate-900">Codeshub WhatsApp</div>
        {businesses.length > 1 && (
          <select
            value={activeBusiness?.id ?? ""}
            onChange={(e) => setActiveBusinessId(Number(e.target.value))}
            className="mt-2 w-full rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-700 focus:outline-none"
          >
            {businesses.map((b) => (
              <option key={b.id} value={b.id}>
                {b.business_name}
              </option>
            ))}
          </select>
        )}
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "block rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-emerald-50 text-emerald-700" : "text-slate-600 hover:bg-slate-100"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-slate-200 px-5 py-4">
        <div className="text-sm font-medium text-slate-800">{user?.name}</div>
        <div className="text-xs text-slate-500">{user?.email}</div>
        <button
          onClick={() => {
            logout();
            router.replace("/login");
          }}
          className="mt-3 text-sm font-medium text-red-600 hover:text-red-700"
        >
          Log out
        </button>
      </div>
    </aside>
  );
}