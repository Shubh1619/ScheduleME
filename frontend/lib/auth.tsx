"use client";

import { createContext, useContext, useEffect, useState } from "react";

import { apiFetch } from "./api";
import type { Business, TokenResponse, User } from "./types";

const TOKEN_KEY = "wa_token";
const BUSINESS_KEY = "wa_business_id";

type AuthContextValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  businesses: Business[];
  activeBusiness: Business | null;
  setActiveBusinessId: (id: number) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, businessName?: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function readStorage(key: string): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => readStorage(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [activeBusinessId, setActiveBusinessIdState] = useState<number | null>(() => {
    const raw = readStorage(BUSINESS_KEY);
    return raw ? Number(raw) : null;
  });
  const [loading, setLoading] = useState(() => readStorage(TOKEN_KEY) !== null);

  useEffect(() => {
    if (!token) return;
    apiFetch<User>("/api/v1/auth/me", { token })
      .then((me) => {
        setUser(me);
        return apiFetch<Business[]>("/api/v1/businesses", { token });
      })
      .then(setBusinesses)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const activeBusiness =
    businesses.find((b) => b.id === activeBusinessId) ?? businesses[0] ?? null;

  function setActiveBusinessId(id: number) {
    localStorage.setItem(BUSINESS_KEY, String(id));
    setActiveBusinessIdState(id);
  }

  async function login(email: string, password: string) {
    const res = await apiFetch<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    const list = await apiFetch<Business[]>("/api/v1/businesses", { token: res.access_token });
    localStorage.setItem(TOKEN_KEY, res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    setBusinesses(list);
  }

  async function register(name: string, email: string, password: string, businessName?: string) {
    const res = await apiFetch<TokenResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password, business_name: businessName }),
    });
    const list = await apiFetch<Business[]>("/api/v1/businesses", { token: res.access_token });
    localStorage.setItem(TOKEN_KEY, res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    setBusinesses(list);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(BUSINESS_KEY);
    setToken(null);
    setUser(null);
    setBusinesses([]);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        businesses,
        activeBusiness,
        setActiveBusinessId,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}