"use client";

import type { AuthUser, AuthResponse } from "./types";
import api from "./api";
import { supabase } from "./supabaseClient";

export function saveSession(data: AuthResponse) {
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  localStorage.setItem("user", JSON.stringify(data.user));
}

export function clearSession() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("user");
  return raw ? (JSON.parse(raw) as AuthUser) : null;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/auth/login", { email, password });
  saveSession(data);
  return data;
}

export async function register(
  email: string,
  password: string,
  role: "job_seeker" | "company_admin",
  full_name?: string
): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>("/auth/register", {
    email,
    password,
    role,
    full_name,
  });
  saveSession(data);
  return data;
}

export async function logout() {
  await api.post("/auth/logout").catch(() => {});
  clearSession();
}

export async function signInWithGoogle() {
  // Always use a clean redirect URL — no query params.
  // Supabase PKCE state validation requires the redirectTo to match exactly what's
  // whitelisted in the Supabase dashboard. The role is preserved via localStorage
  // (pending_oauth_role) and read in the callback page.
  const redirectTo = `${window.location.origin}/auth/callback`;

  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo },
  });
  if (error) throw error;
}

export async function exchangeCodeForSession(
  code: string,
  role?: "job_seeker" | "company_admin"
): Promise<AuthResponse> {
  const { data, error } = await supabase.auth.exchangeCodeForSession(code);
  if (error || !data.session) {
    throw error ?? new Error("No session returned from Supabase");
  }

  const { access_token, refresh_token } = data.session;

  clearSession();
  const { data: user } = await api.post<AuthUser>(
    "/auth/oauth/sync",
    { role },
    { headers: { Authorization: `Bearer ${access_token}` } }
  );

  const authResponse: AuthResponse = { access_token, refresh_token, user };
  saveSession(authResponse);
  return authResponse;
}
