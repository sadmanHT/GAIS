"use client";

import { useEffect, useMemo, useState } from "react";
import { getMockTest, MockTestResponse } from "@/lib/api";

const USER_ID = "demo-user";

export default function TestPage() {
  const [mockTest, setMockTest] = useState<MockTestResponse | null>(null);
  const [started, setStarted] = useState(false);
  const [sectionIndex, setSectionIndex] = useState(0);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setMockTest(await getMockTest(USER_ID));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load mock test.");
      }
    }

    void load();
  }, []);

  const currentSection = mockTest?.sections[sectionIndex];
  const currentQuestion = currentSection?.questions[questionIndex];
  const totalQuestions = useMemo(
    () => mockTest?.sections.reduce((sum, section) => sum + section.questions.length, 0) ?? 0,
    [mockTest],
  );

  function nextQuestion() {
    if (!currentSection) return;
    if (questionIndex + 1 < currentSection.questions.length) {
      setQuestionIndex((value) => value + 1);
      return;
    }
    if (mockTest && sectionIndex + 1 < mockTest.sections.length) {
      setSectionIndex((value) => value + 1);
      setQuestionIndex(0);
      return;
    }
    setStarted(false);
    setSectionIndex(0);
    setQuestionIndex(0);
  }

  if (started) {
    return (
      <main className="test-shell">
        <div className="test-top">
          <span>SECTION {sectionIndex + 1} OF {mockTest?.sections.length ?? 3} - {currentSection?.title ?? "LOADING"}</span>
          <span className="timer">{currentSection?.duration_minutes ?? 30}:00</span>
          <span>QUESTION {questionIndex + 1} OF {currentSection?.questions.length ?? 0}</span>
        </div>
        <div className="study-stage" style={{ paddingTop: 48 }}>
          <div className="study-meta">{currentQuestion?.topic ?? "Practice"} - {currentQuestion?.difficulty ?? "adaptive"}</div>
          <p className="q-prompt">{currentQuestion?.content ?? "Loading question..."}</p>
          <div className="choices">
            {["Quantity A is greater.", "Quantity B is greater.", "The two quantities are equal.", "The relationship cannot be determined."].map((choice, index) => (
              <button className="choice" key={choice} type="button">
                <span className="l">{String.fromCharCode(97 + index)}.</span>
                <span>{choice}</span>
                <span className="mark" />
              </button>
            ))}
          </div>
          <div className="study-actions">
            <button className="btn text" type="button" onClick={() => setStarted(false)}>Exit test</button>
            <button className="btn" type="button" onClick={nextQuestion}>Next -&gt;</button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="test-cover">
      <div className="eyebrow" style={{ marginBottom: 24 }}>Mock test - adaptive simulation</div>
      <h1 className="test-cover-h">A full <em>simulated GRE.</em></h1>
      <p className="diag-deck" style={{ marginBottom: 48 }}>
        Three sections, timed pressure, and model-selected practice. Once you start, keep the rhythm.
      </p>

      {error ? <div className="q-context" style={{ color: "var(--accent)" }}>{error}</div> : null}

      <div>
        {(mockTest?.sections ?? []).map((section, index) => (
          <div className="test-sect" key={section.title}>
            <b>{index + 1}. {section.title}</b>
            <span>{section.questions.length} questions - {section.duration_minutes} minutes</span>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 64, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 24 }}>
        <span className="italic-note">{totalQuestions || "Loading"} questions prepared from the backend question bank.</span>
        <button className="btn" type="button" disabled={!mockTest} onClick={() => setStarted(true)}>
          Begin -&gt;
        </button>
      </div>
    </main>
  );
}
