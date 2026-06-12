"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import api from "@/lib/api";
import { getToken } from "@/lib/auth";

type DiscordStatus = {
  connected: boolean;
  discord_username: string | null;
  channel_id: string | null;
  guild_id: string | null;
  is_active: boolean;
  bot_invite_url: string;
};

type Step = "idle" | "invite_bot" | "enter_channel" | "done";

export default function SettingsPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<DiscordStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState<Step>("idle");
  const [channelId, setChannelId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const authHeader = () => ({ Authorization: `Bearer ${getToken()}` });

  const fetchStatus = async () => {
    try {
      const { data } = await api.get<DiscordStatus>("/discord/status", {
        headers: authHeader(),
      });
      setStatus(data);
      if (data.connected && data.channel_id) setStep("done");
      else if (data.connected && !data.channel_id) setStep("invite_bot");
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const result = searchParams.get("discord");
    if (result === "connected") setStep("invite_bot");
    if (result === "error") setError("Discord connection failed. Please try again.");
  }, [searchParams]);

  const handleConnect = async () => {
    try {
      const { data } = await api.get<{ url: string }>("/discord/connect", {
        headers: authHeader(),
      });
      window.location.href = data.url;
    } catch {
      setError("Could not start Discord connection.");
    }
  };

  const handleSaveChannel = async () => {
    if (!channelId.trim()) return;
    setSaving(true);
    setError("");
    try {
      await api.post(
        "/discord/setup",
        { channel_id: channelId.trim() },
        { headers: authHeader() }
      );
      await fetchStatus();
      setStep("done");
    } catch {
      setError("Failed to save channel. Make sure the bot is in your server and the channel ID is correct.");
    } finally {
      setSaving(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await api.delete("/discord/disconnect", { headers: authHeader() });
      setStep("idle");
      setChannelId("");
      await fetchStatus();
    } catch {
      setError("Failed to disconnect.");
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-slate-400 text-sm">Loading settings…</div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 text-sm mt-1">Manage your integrations and preferences.</p>
      </div>

      {/* Discord Integration Card */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center gap-3">
          {/* Discord logo */}
          <svg viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7 text-indigo-400">
            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z" />
          </svg>
          <div>
            <h2 className="text-lg font-semibold text-white">Discord Job Alerts</h2>
            <p className="text-slate-400 text-sm">Get daily job matches sent to your Discord server at 14:00.</p>
          </div>
          {step === "done" && (
            <span className="ml-auto text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">Active</span>
          )}
          {status?.connected && step !== "done" && (
            <span className="ml-auto text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded-full">Setup needed</span>
          )}
        </div>

        {error && (
          <p className="text-red-400 text-sm bg-red-500/10 rounded p-3">{error}</p>
        )}

        {/* Step: not connected */}
        {step === "idle" && (
          <div className="space-y-3">
            <p className="text-slate-300 text-sm">Connect your Discord account to enable daily job alerts in your server.</p>
            <button
              onClick={handleConnect}
              className="btn-primary flex items-center gap-2"
            >
              Connect Discord
            </button>
          </div>
        )}

        {/* Step: connected, invite bot */}
        {step === "invite_bot" && status && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-green-400 text-sm">
              <span>✓</span>
              <span>Connected as <strong>{status.discord_username}</strong></span>
            </div>

            <div className="space-y-3 border border-slate-700 rounded-lg p-4">
              <p className="text-white font-medium text-sm">Step 1 — Add the bot to your server</p>
              <p className="text-slate-400 text-sm">Click the button below to invite the CV Intelligence bot to your Discord server. Make sure to grant it permission to send messages.</p>
              <a
                href={status.bot_invite_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary inline-flex items-center gap-2 text-sm"
              >
                Invite Bot to Server
              </a>
            </div>

            <div className="space-y-3 border border-slate-700 rounded-lg p-4">
              <p className="text-white font-medium text-sm">Step 2 — Copy your channel ID</p>
              <ol className="text-slate-400 text-sm space-y-1 list-decimal list-inside">
                <li>Open Discord and go to <strong>Settings → Advanced</strong></li>
                <li>Enable <strong>Developer Mode</strong></li>
                <li>Right-click the channel you want alerts in</li>
                <li>Click <strong>Copy Channel ID</strong></li>
              </ol>
            </div>

            <div className="space-y-3 border border-slate-700 rounded-lg p-4">
              <p className="text-white font-medium text-sm">Step 3 — Paste your channel ID</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={channelId}
                  onChange={(e) => setChannelId(e.target.value)}
                  placeholder="e.g. 1234567890123456789"
                  className="input flex-1"
                />
                <button
                  onClick={handleSaveChannel}
                  disabled={saving || !channelId.trim()}
                  className="btn-primary disabled:opacity-50"
                >
                  {saving ? "Saving…" : "Save"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step: fully configured */}
        {step === "done" && status && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-green-400 text-sm">
              <span>✓</span>
              <span>Connected as <strong>{status.discord_username}</strong></span>
            </div>
            <div className="text-slate-400 text-sm space-y-1">
              <p>Channel ID: <code className="text-slate-300">{status.channel_id}</code></p>
              <p>Job alerts are sent daily at <strong className="text-white">14:00 Israel time</strong>.</p>
            </div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => { setStep("invite_bot"); setChannelId(""); }}
                className="btn-secondary text-sm"
              >
                Change Channel
              </button>
              <button
                onClick={handleDisconnect}
                className="text-red-400 text-sm hover:text-red-300 transition-colors"
              >
                Disconnect Discord
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
