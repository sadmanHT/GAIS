"use client";

import { useEffect, useState } from "react";
import { DiagnosticInsightResponse, getDiagnostic } from "@/lib/api";

const USER_ID = "demo-user";

export default function DiagnosticPage() {
  const [diagnostic, setDiagnostic] = useState<DiagnosticInsightResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setDiagnostic(await getDiagnostic(USER_ID));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load insights.");
      }
    }

    void load();
  }, []);

  return (
    <main className="diag">
      <div className="diag-eyebrow">Insights - updated from your latest answers</div>
      <h1 className="diag-h">A pattern in <em>your recent study</em>.</h1>
      <p className="diag-deck">
        {diagnostic?.summary ?? "GAIS is reading the signal from your knowledge, retention, and behaviour models."}
      </p>

      {error ? <div className="q-context" style={{ color: "var(--accent)" }}>{error}</div> : null}

      {(diagnostic?.findings ?? []).map((finding, index) => (
        <section className="diag-section" key={finding.title}>
          <div className="diag-section-h">
            FINDING {index + 1} - {finding.severity.toUpperCase()}
          </div>
          <div className="diag-finding">
            <p className="quote">{finding.title}</p>
            <p className="meta">{finding.detail}</p>
          </div>
        </section>
      ))}

      {!diagnostic?.findings.length ? (
        <p className="italic-note">Complete a short session and insights will appear here.</p>
      ) : null}
    </main>
  );
}
