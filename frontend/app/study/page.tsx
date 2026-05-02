"use client";

/* eslint-disable react-hooks/purity, react-hooks/set-state-in-effect */

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getNextQuestion, NextQuestionResponse, submitAnswer, SubmitAnswerResponse } from "@/lib/api";

const USER_ID = "demo-user";
const ANSWER_OPTIONS = ["A focused answer", "A tempting distractor", "A broader guess", "None of these"];

function formatSeconds(total: number) {
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

export default function StudyPage() {
  const [question, setQuestion] = useState<NextQuestionResponse | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<SubmitAnswerResponse | null>(null);
  const [startedAt, setStartedAt] = useState(Date.now());
  const [seconds, setSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const loadQuestion = useCallback(async () => {
    setError(null);
    setSelected(null);
    setConfidence(null);
    setFeedback(null);
    setSeconds(0);
    try {
      const next = await getNextQuestion(USER_ID);
      setQuestion(next);
      setStartedAt(Date.now());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load the next question.");
    }
  }, []);

  useEffect(() => {
    void loadQuestion();
  }, [loadQuestion]);

  useEffect(() => {
    const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [question?.question_id]);

  const correct = selected === 0;
  const canSubmit = selected !== null && confidence !== null && !feedback;
  const questionLabel = useMemo(
    () => question ? `${question.topic} · ${question.difficulty}` : "Loading",
    [question],
  );

  async function submitSelected() {
    if (!question || !canSubmit || selected === null || confidence === null) return;
    const responseTimeMs = Math.max(Date.now() - startedAt, 250);
    try {
      const result = await submitAnswer(USER_ID, question.question_id, correct, responseTimeMs, confidence);
      setFeedback(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit your answer.");
    }
  }

  return (
    <main className="study-shell">
      <div className="study-bar">
        <Link href="/" className="hover:text-[var(--ink)]">← Leave session</Link>
        <span><b>{question?.question_id ?? "—"}</b> · {questionLabel}</span>
        <span>{formatSeconds(seconds)}</span>
      </div>

      <section className="study-stage">
        <div className="study-meta">Multiple choice</div>

        {error ? (
          <div className="q-context" style={{ color: "var(--accent)" }}>{error}</div>
        ) : null}

        <p className="q-prompt">{question?.content ?? "Preparing the next question…"}</p>
        {question?.hint ? <div className="q-context">{question.hint}</div> : null}

        <div className="choices">
          {ANSWER_OPTIONS.map((option, index) => {
            let className = "choice";
            if (selected === index && !feedback) className += " sel";
            if (feedback && index === 0) className += " right";
            if (feedback && selected === index && index !== 0) className += " wrong";

            return (
              <button
                key={option}
                type="button"
                className={className}
                disabled={!!feedback}
                onClick={() => setSelected(index)}
              >
                <span className="l">{String.fromCharCode(97 + index)}.</span>
                <span>{option}</span>
                <span className="mark">
                  {feedback && index === 0 ? "✓" : feedback && selected === index ? "×" : selected === index ? "●" : ""}
                </span>
              </button>
            );
          })}
        </div>

        {!feedback ? (
          <>
            <div className="conf-row">
              <span>How sure are you?</span>
              <div className="conf-pips">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button
                    key={value}
                    type="button"
                    className={`conf-pip ${confidence === value ? "on" : ""}`}
                    onClick={() => setConfidence(value)}
                  >
                    {value}
                  </button>
                ))}
              </div>
            </div>
            <div className="study-actions">
              <button className="btn text" type="button" onClick={() => void loadQuestion()}>
                Skip this one
              </button>
              <button className="btn" type="button" disabled={!canSubmit} style={{ opacity: canSubmit ? 1 : 0.4 }} onClick={() => void submitSelected()}>
                Submit <span>→</span>
              </button>
            </div>
          </>
        ) : (
          <div className="feedback">
            <div className={`verdict ${correct ? "ok" : "no"}`}>
              {correct ? "That’s right." : "Not quite — the first option is the placeholder correct answer."}
            </div>
            <p className="body">
              Engagement {Math.round(feedback.engagement_score * 100)}% · Mastery{" "}
              {Math.round(feedback.mastery_probability * 100)}% · Retention{" "}
              {Math.round(feedback.retention_score * 100)}%
            </p>
            <div className="study-actions">
              <Link className="btn text" href="/dashboard">View progress</Link>
              <button className="btn" type="button" onClick={() => void loadQuestion()}>
                Next <span>→</span>
              </button>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
