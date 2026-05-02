"use client";

import { useEffect, useState } from "react";
import { getSettings, updateSettings, UserSettingsResponse } from "@/lib/api";

const USER_ID = "demo-user";

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettingsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setSettings(await getSettings(USER_ID));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load settings.");
      }
    }

    void load();
  }, []);

  async function setValue(update: Partial<UserSettingsResponse>) {
    if (!settings) return;
    const optimistic = { ...settings, ...update };
    setSettings(optimistic);
    try {
      setSettings(await updateSettings(USER_ID, update));
    } catch (err) {
      setSettings(settings);
      setError(err instanceof Error ? err.message : "Could not save settings.");
    }
  }

  return (
    <main className="set">
      <div className="eyebrow" style={{ marginBottom: 8 }}>Settings</div>
      <h1 className="h-l" style={{ marginBottom: 64 }}>Quiet preferences.</h1>

      {error ? <div className="q-context" style={{ color: "var(--accent)" }}>{error}</div> : null}

      <section className="set-group">
        <div className="set-group-h">STUDY</div>
        <div className="set-row">
          <div className="lab">Time pressure simulation
            <small>An adaptive timer that tightens as you improve. Replicates real test conditions.</small>
          </div>
          <button
            aria-label="Toggle time pressure"
            className={`tog ${settings?.time_pressure ? "on" : ""}`}
            type="button"
            onClick={() => setValue({ time_pressure: !settings?.time_pressure })}
          />
        </div>
        <div className="set-row">
          <div className="lab">Audio cues
            <small>A soft tone on submit. Keep it off if it breaks your concentration.</small>
          </div>
          <button
            aria-label="Toggle audio cues"
            className={`tog ${settings?.audio_cues ? "on" : ""}`}
            type="button"
            onClick={() => setValue({ audio_cues: !settings?.audio_cues })}
          />
        </div>
        <div className="set-row">
          <div className="lab">Daily session length
            <small>How long you want sessions to be on a typical weekday.</small>
          </div>
          <button
            className="val"
            type="button"
            onClick={() => setValue({ daily_session_minutes: settings?.daily_session_minutes === 25 ? 40 : 25 })}
          >
            {settings?.daily_session_minutes ?? 25} minutes -&gt;
          </button>
        </div>
      </section>

      <section className="set-group">
        <div className="set-group-h">GOAL</div>
        <div className="set-row">
          <div className="lab">Target score<small>Used to set the intensity of study plans.</small></div>
          <button className="val" type="button" onClick={() => setValue({ target_score: settings?.target_score === 332 ? 325 : 332 })}>
            {settings?.target_score ?? 332} -&gt;
          </button>
        </div>
        <div className="set-row">
          <div className="lab">Weakest area<small>Seed value from onboarding; live progress will override it.</small></div>
          <button className="val" type="button" onClick={() => setValue({ weakest_area: settings?.weakest_area === "Quant" ? "Verbal" : "Quant" })}>
            {settings?.weakest_area ?? "Not set"} -&gt;
          </button>
        </div>
      </section>

      <section className="set-group">
        <div className="set-group-h">EMAIL</div>
        <div className="set-row">
          <div className="lab">Weekly summary
            <small>Sundays at 9am. What you learned, what is drifting.</small>
          </div>
          <button
            aria-label="Toggle weekly summary"
            className={`tog ${settings?.weekly_summary ? "on" : ""}`}
            type="button"
            onClick={() => setValue({ weekly_summary: !settings?.weekly_summary })}
          />
        </div>
      </section>
    </main>
  );
}
