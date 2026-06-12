import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const FRIENDLY_ERRORS: Record<string, string> = {
  "User already registered":
    "An account with this email already exists. Try logging in instead.",
  "User not allowed":
    "Registration is temporarily unavailable. Please try again in a moment.",
  "Password should be at least 6 characters":
    "Your password must be at least 6 characters long.",
  "Unable to validate email address: invalid format":
    "Please enter a valid email address.",
  "Invalid login credentials":
    "Incorrect email or password.",
  "ERR_NETWORK":
    "Cannot reach the server. Make sure the backend is running.",
};

export function friendlyError(raw: string): string {
  for (const [key, msg] of Object.entries(FRIENDLY_ERRORS)) {
    if (raw.includes(key)) return msg;
  }
  return raw;
}

export function authErrorFrom(err: unknown, fallback: string): string {
  const e = err as { code?: string; response?: { data?: { detail?: string } } };
  const raw = e?.response?.data?.detail ?? e?.code ?? fallback;
  return friendlyError(raw);
}
