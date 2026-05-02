"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { submitOnboarding } from "@/lib/api";

const USER_ID = "demo-user";

const targets = [
  { value: 315, label: "A solid score", sub: "70th percentile" },
  { value: 325, label: "Competitive", sub: "85th percentile" },
  { value: 332, label: "Top tier", sub: "95th percentile" },
  { value: 338, label: "Aiming for the top", sub: "99th+" },
];

const weakAreas = [
  { value: "Quant", label: "Quant", sub: "especially the harder stuff" },
  { value: "Verbal", label: "Verbal", sub: "vocab and reading" },
  { value: "Unknown", label: "Honestly, I am not sure", sub: "let the model find it" },
];

export default function OnboardPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [targetScore, setTargetScore] = useState<number | null>(332);
  const [testDate, setTestDate] = useState("March 17, 2026");
  const [weakestArea, setWeakestArea] = useState<string | null>("Quant");
  const [error, setError] = useState<string | null>(null);

  async function finish() {
    try {
      await submitOnboarding(USER_ID, {
        target_score: targetScore,
        test_date: testDate,
        weakest_area: weakestArea,
      });
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save onboarding.");
    }
  }

  if (step === 0) {
    return (
      <main className="onb">
        <div className="onb-step">Step 1 of 3</div>
        <h1 className="onb-q">What score are you <em>really</em> after?</h1>
        <div className="onb-options">
          {targets.map((target) => (
            <button
              className={`onb-opt ${targetScore === target.value ? "sel" : ""}`}
              key={target.value}
              type="button"
              onClick={() => setTargetScore(target.value)}
            >
              <span>{target.label}<small>{target.sub}</small></span>
              <small>{target.value}</small>
            </button>
          ))}
        </div>
        <div className="onb-foot">
          <span>Be honest. We will calibrate from here.</span>
          <button className="btn" disabled={!targetScore} type="button" onClick={() => setStep(1)}>
            Continue -&gt;
          </button>
        </div>
      </main>
    );
  }

  if (step === 1) {
    return (
      <main className="onb">
        <div className="onb-step">Step 2 of 3</div>
        <h1 className="onb-q">When is the test?</h1>
        <input className="onb-input" value={testDate} onChange={(event) => setTestDate(event.target.value)} />
        <p className="italic-note" style={{ marginTop: 16 }}>That gives GAIS a horizon for review urgency.</p>
        <div className="onb-foot">
          <button className="btn text" type="button" onClick={() => setStep(0)}>&lt;- Back</button>
          <button className="btn" type="button" onClick={() => setStep(2)}>Continue -&gt;</button>
        </div>
      </main>
    );
  }

  return (
    <main className="onb">
      <div className="onb-step">Step 3 of 3</div>
      <h1 className="onb-q">One last thing.</h1>
      <p className="diag-deck" style={{ marginBottom: 32 }}>
        Where do you feel weakest right now? It is fine to guess; the models will correct course as you answer.
      </p>
      <div className="onb-options">
        {weakAreas.map((area) => (
          <button
            className={`onb-opt ${weakestArea === area.value ? "sel" : ""}`}
            key={area.value}
            type="button"
            onClick={() => setWeakestArea(area.value)}
          >
            <span>{area.label}<small>{area.sub}</small></span>
          </button>
        ))}
      </div>
      {error ? <p className="q-context" style={{ color: "var(--accent)" }}>{error}</p> : null}
      <div className="onb-foot">
        <button className="btn text" type="button" onClick={() => setStep(1)}>&lt;- Back</button>
        <button className="btn" type="button" onClick={finish}>Begin -&gt;</button>
      </div>
    </main>
  );
}
