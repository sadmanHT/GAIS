"use client";

import { useEffect, useMemo, useState } from "react";
import { getUserProgress, UserProgressResponse } from "@/lib/api";

const USER_ID = "demo-user";

function barClass(value: number) {
  if (value < 0.6) return "skill-bar weak";
  if (value > 0.8) return "skill-bar strong";
  return "skill-bar";
}

export default function DashboardPage() {
  const [progress, setProgress] = useState<UserProgressResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setProgress(await getUserProgress(USER_ID));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load progress.");
      }
    }

    void load();
  }, []);

  const concepts = useMemo(
    () => [...(progress?.concepts ?? [])].sort((a, b) => a.mastery_probability - b.mastery_probability),
    [progress],
  );

  const accuracy = Math.round((progress?.overall_accuracy ?? 0) * 100);

  return (
    <main className="prog">
      <div className="prog-head">
        <div>
          <div className="eyebrow" style={{ marginBottom: 8 }}>Progress</div>
          <h1 className="h-l">A steady climb.</h1>
        </div>
        <div className="small italic-note">Live mastery · from your recent answers</div>
      </div>

      <section className="prog-chart-wrap">
        <div className="prog-chart-h">
          <div>
            <div className="num">{accuracy}<small>%</small></div>
            <div className="small">Overall accuracy</div>
          </div>
          <div className="small">
            {progress?.total_questions_answered ?? 0} questions · {progress?.weakest_concepts.length ?? 0} weak concepts
          </div>
        </div>
      </section>

      {error ? <div className="q-context" style={{ color: "var(--accent)" }}>{error}</div> : null}

      <div className="skill-list">
        {concepts.length ? concepts.map((concept) => {
          const pct = Math.round(concept.mastery_probability * 100);
          return (
            <div className="skill-row" key={concept.concept}>
              <div className="skill-name">
                {concept.concept}
                <small>{pct < 60 ? "Needs work" : pct > 80 ? "Solid" : "Steady"}</small>
              </div>
              <div className={barClass(concept.mastery_probability)}>
                <div className="f" style={{ width: `${pct}%` }} />
              </div>
              <div className="skill-val">{pct}%</div>
            </div>
          );
        }) : (
          <p className="italic-note">Answer a few questions and your concept map will appear here.</p>
        )}
      </div>

      {progress?.weakest_concepts.length ? (
        <section className="focal" style={{ marginTop: 72 }}>
          <div className="eyebrow" style={{ marginBottom: 12 }}>Weakest three</div>
          <h2 className="focal-title">
            {progress.weakest_concepts.map((concept) => concept.concept).join(", ")}.
          </h2>
          <div className="focal-meta">These should drive the next short review block.</div>
        </section>
      ) : null}
    </main>
  );
}
