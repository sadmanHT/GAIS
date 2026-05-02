"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  getRecommendation,
  getUserProgress,
  RecommendationResponse,
  StudyPlanItem,
  UserProgressResponse,
} from "@/lib/api";

const DEFAULT_USER_ID = "demo-user";
const USER_ID_KEY = "gais-user-id";
const STUDY_DAYS_KEY = "gais-study-days";
const DAILY_QUESTION_COUNTS_KEY = "gais-daily-question-counts";

type EnrichedStudyItem = StudyPlanItem & {
  retention: number;
  estimatedMinutes: number;
};

function toLocalDateKey(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function prettyDate(date: Date) {
  return new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(date);
}

function greetingForHour(hour: number) {
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function urgencyStyles(urgency: string) {
  if (urgency === "high") {
    return {
      border: "border-red-500/80",
      badge: "bg-red-500/15 text-red-200 ring-1 ring-red-400/30",
      dot: "bg-red-400",
      card: "from-red-500/12 via-white/5 to-white/0",
    };
  }

  if (urgency === "medium") {
    return {
      border: "border-amber-400/80",
      badge: "bg-amber-400/15 text-amber-100 ring-1 ring-amber-300/30",
      dot: "bg-amber-300",
      card: "from-amber-500/10 via-white/5 to-white/0",
    };
  }

  return {
    border: "border-emerald-500/70",
    badge: "bg-emerald-500/15 text-emerald-100 ring-1 ring-emerald-400/30",
    dot: "bg-emerald-300",
    card: "from-emerald-500/10 via-white/5 to-white/0",
  };
}

function actionLabel(action: string) {
  return action === "revise" ? "Revise" : "Practice new";
}

function actionStyles(action: string) {
  return action === "revise"
    ? "bg-sky-400/15 text-sky-100 ring-1 ring-sky-300/30"
    : "bg-violet-400/15 text-violet-100 ring-1 ring-violet-300/30";
}

function splitStudyDays(value: string | null) {
  if (!value) return [] as string[];

  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [] as string[];
  }
}

function readDailyCounts(value: string | null) {
  if (!value) return {} as Record<string, number>;

  try {
    const parsed = JSON.parse(value);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return Object.fromEntries(
        Object.entries(parsed).flatMap(([key, count]) => {
          if (typeof count !== "number" || Number.isNaN(count)) return [];
          return [[key, count]];
        }),
      ) as Record<string, number>;
    }
  } catch {
    return {} as Record<string, number>;
  }

  return {} as Record<string, number>;
}

function getWeekDays(baseDate: Date) {
  const start = new Date(baseDate);
  const day = start.getDay();
  const offset = day === 0 ? -6 : 1 - day;
  start.setDate(start.getDate() + offset);

  return Array.from({ length: 7 }, (_, index) => {
    const current = new Date(start);
    current.setDate(start.getDate() + index);
    return current;
  });
}

function matchConcept(progress: UserProgressResponse | null, topic: string) {
  const normalizedTopic = topic.trim().toLowerCase();
  return progress?.concepts.find((concept) => concept.concept.trim().toLowerCase() === normalizedTopic);
}

function retentionForItem(item: StudyPlanItem, progress: UserProgressResponse | null) {
  const matchedConcept = matchConcept(progress, item.topic);
  if (matchedConcept) {
    return Math.round(matchedConcept.mastery_probability * 100);
  }

  return item.urgency === "high" ? 42 : item.urgency === "medium" ? 64 : 82;
}

function estimatedMinutesForItem(item: StudyPlanItem, retention: number) {
  const urgencyBase = item.urgency === "high" ? 18 : item.urgency === "medium" ? 13 : 9;
  const adjustment = Math.max(0, Math.round((70 - retention) / 10));
  return urgencyBase + adjustment;
}

function currentStreak(studyDays: Set<string>, today: Date) {
  let streak = 0;
  const cursor = new Date(today);

  while (studyDays.has(toLocalDateKey(cursor))) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }

  return streak;
}

function persistStudyDay() {
  if (typeof window === "undefined") return;

  const todayKey = toLocalDateKey(new Date());
  const studyDays = new Set(splitStudyDays(window.localStorage.getItem(STUDY_DAYS_KEY)));
  studyDays.add(todayKey);
  const nextStudyDays = Array.from(studyDays).sort();
  window.localStorage.setItem(STUDY_DAYS_KEY, JSON.stringify(nextStudyDays));

  const counts = readDailyCounts(window.localStorage.getItem(DAILY_QUESTION_COUNTS_KEY));
  counts[todayKey] = (counts[todayKey] ?? 0) + 1;
  window.localStorage.setItem(DAILY_QUESTION_COUNTS_KEY, JSON.stringify(counts));

  return {
    studyDays: nextStudyDays,
    dailyCounts: counts,
  };
}

export default function PlanPage() {
  const [userId] = useState(() => {
    if (typeof window === "undefined") return DEFAULT_USER_ID;
    const storedUserId = window.localStorage.getItem(USER_ID_KEY);
    if (!storedUserId) {
      window.localStorage.setItem(USER_ID_KEY, DEFAULT_USER_ID);
      return DEFAULT_USER_ID;
    }

    return storedUserId;
  });
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [progress, setProgress] = useState<UserProgressResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [studyDays, setStudyDays] = useState<string[]>(() => {
    if (typeof window === "undefined") return [];
    return splitStudyDays(window.localStorage.getItem(STUDY_DAYS_KEY));
  });
  const [dailyCounts, setDailyCounts] = useState<Record<string, number>>(() => {
    if (typeof window === "undefined") return {};
    return readDailyCounts(window.localStorage.getItem(DAILY_QUESTION_COUNTS_KEY));
  });
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setError(null);
        const [recommendationResponse, progressResponse] = await Promise.all([
          getRecommendation(userId),
          getUserProgress(userId),
        ]);

        if (!active) return;
        setRecommendation(recommendationResponse);
        setProgress(progressResponse);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Could not load the plan.");
      }
    }

    void load();

    return () => {
      active = false;
    };
  }, [userId]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  const today = useMemo(() => new Date(now), [now]);
  const dateLabel = useMemo(() => prettyDate(today), [today]);
  const greeting = useMemo(() => greetingForHour(today.getHours()), [today]);
  const weekDays = useMemo(() => getWeekDays(today), [today]);
  const studyDaySet = useMemo(() => new Set(studyDays), [studyDays]);
  const streak = useMemo(() => currentStreak(studyDaySet, today), [studyDaySet, today]);
  const totalQuestionsToday = dailyCounts[toLocalDateKey(today)] ?? 0;
  const averageMastery = useMemo(() => {
    if (!progress?.concepts.length) return Math.round((progress?.overall_accuracy ?? 0) * 100);
    const total = progress.concepts.reduce((sum, concept) => sum + concept.mastery_probability, 0);
    return Math.round((total / progress.concepts.length) * 100);
  }, [progress]);

  const items = useMemo<EnrichedStudyItem[]>(() => {
    const plan = recommendation?.study_plan ?? [];
    return plan.map((item) => {
      const retention = retentionForItem(item, progress);
      return {
        ...item,
        retention,
        estimatedMinutes: estimatedMinutesForItem(item, retention),
      };
    });
  }, [progress, recommendation]);

  const primaryItems = useMemo(() => {
    const highUrgency = items.filter((item) => item.urgency === "high");
    if (highUrgency.length > 0) return highUrgency;
    return items.slice(0, Math.min(2, items.length));
  }, [items]);

  const primaryTopics = useMemo(() => new Set(primaryItems.map((item) => item.topic)), [primaryItems]);
  const comingUpItems = useMemo(
    () => items.filter((item) => !primaryTopics.has(item.topic) && item.urgency !== "high"),
    [items, primaryTopics],
  );

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.18),_transparent_35%),linear-gradient(180deg,_#07111f_0%,_#09131f_46%,_#050a13_100%)] px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <section className="overflow-hidden rounded-[2rem] border border-white/10 bg-white/6 p-6 shadow-2xl shadow-black/20 backdrop-blur-xl sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.28em] text-slate-400">{dateLabel}</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                {greeting}, {userId === DEFAULT_USER_ID ? "there" : userId}.
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">
                Your plan is built from the latest recommendation signal and your live mastery snapshot.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:min-w-[28rem]">
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Current streak</p>
                <p className="mt-2 text-2xl font-semibold text-white">{streak} days</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Questions today</p>
                <p className="mt-2 text-2xl font-semibold text-white">{totalQuestionsToday}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Average mastery</p>
                <p className="mt-2 text-2xl font-semibold text-white">{averageMastery}%</p>
              </div>
            </div>
          </div>

          <div className="mt-6 rounded-3xl border border-white/10 bg-black/15 p-4">
            <div className="flex items-center justify-between gap-4">
              <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-400">This week</p>
              <p className="text-xs text-slate-400">Green means you studied that day.</p>
            </div>
            <div className="mt-4 grid grid-cols-7 gap-2 sm:gap-3">
              {weekDays.map((day) => {
                const key = toLocalDateKey(day);
                const studied = studyDaySet.has(key);
                return (
                  <div
                    key={key}
                    className={`flex min-h-24 flex-col justify-between rounded-2xl border px-3 py-3 text-left transition ${
                      studied ? "border-emerald-400/30 bg-emerald-400/10" : "border-white/10 bg-white/5"
                    }`}
                  >
                    <div>
                      <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-400">
                        {new Intl.DateTimeFormat(undefined, { weekday: "short" }).format(day)}
                      </p>
                      <p className="mt-2 text-lg font-semibold text-white">{day.getDate()}</p>
                    </div>
                    <span className={`h-2.5 w-2.5 rounded-full ${studied ? "bg-emerald-400" : "bg-slate-500"}`} />
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {error ? (
          <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
            {error}
          </div>
        ) : null}

        <section className="space-y-4">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-400">Today&apos;s focus</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Study session cards</h2>
            </div>
            <p className="max-w-md text-right text-sm text-slate-400">
              The strongest opportunities surface first. Each card shows urgency, retention, and the time to spend.
            </p>
          </div>

          {primaryItems.length > 0 ? (
            <div className="grid gap-4 lg:grid-cols-2">
              {primaryItems.map((item, index) => {
                const styles = urgencyStyles(item.urgency);
                return (
                  <article
                    key={`${item.topic}-${item.action}-${index}`}
                    className={`overflow-hidden rounded-[1.75rem] border border-white/10 bg-gradient-to-br ${styles.card} shadow-xl shadow-black/20`}
                  >
                    <div className={`h-full border-l-4 ${styles.border} p-5 sm:p-6`}>
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 text-white">
                            <h3 className="text-2xl font-semibold tracking-tight">{item.topic}</h3>
                            {item.urgency === "high" ? (
                              <span className={`h-2.5 w-2.5 rounded-full ${styles.dot} animate-pulse`} />
                            ) : null}
                          </div>
                          <div className="mt-3 flex flex-wrap gap-2">
                            <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${actionStyles(item.action)}`}>
                              {actionLabel(item.action)}
                            </span>
                            <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${styles.badge}`}>
                              {item.urgency} urgency
                            </span>
                          </div>
                        </div>

                        <Link
                          href="/study"
                          onClick={() => {
                            const nextState = persistStudyDay();
                            if (nextState) {
                              setStudyDays(nextState.studyDays);
                              setDailyCounts(nextState.dailyCounts);
                            }
                          }}
                          className="inline-flex shrink-0 items-center rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-950 transition hover:scale-[1.02] hover:bg-slate-100"
                        >
                          Start
                        </Link>
                      </div>

                      <div className="mt-6 rounded-2xl border border-white/10 bg-black/20 p-4">
                        <div className="flex items-center justify-between text-sm text-slate-300">
                          <span>Retention</span>
                          <span className="font-semibold text-white">{item.retention}%</span>
                        </div>
                        <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
                          <div
                            className={`h-full rounded-full ${
                              item.urgency === "high"
                                ? "bg-red-400"
                                : item.urgency === "medium"
                                  ? "bg-amber-300"
                                  : "bg-emerald-300"
                            }`}
                            style={{ width: `${Math.min(100, Math.max(10, item.retention))}%` }}
                          />
                        </div>
                      </div>

                      <div className="mt-5 flex flex-wrap items-start gap-3 text-sm text-slate-300">
                        <span className="font-medium text-white">{item.estimatedMinutes} min</span>
                        <span className="h-1 w-1 rounded-full bg-slate-500" />
                        <p className="leading-6 text-slate-300">{item.reason}</p>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="rounded-3xl border border-white/10 bg-white/5 p-6 text-slate-300">
              {recommendation ? "No recommendations yet. Answer a few questions and the plan will fill in here." : "Loading your plan…"}
            </div>
          )}
        </section>

        <section className="rounded-[1.75rem] border border-white/10 bg-white/5 p-5 shadow-xl shadow-black/10 backdrop-blur-xl sm:p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-400">Coming Up</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Lower-urgency topics</h2>
            </div>
            <span className="text-sm text-slate-400">{comingUpItems.length} queued</span>
          </div>

          <div className="mt-5 space-y-3">
            {comingUpItems.length > 0 ? (
              comingUpItems.map((item, index) => {
                const styles = urgencyStyles(item.urgency);
                return (
                  <div
                    key={`${item.topic}-${item.action}-coming-up-${index}`}
                    className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <span className={`h-3 w-3 rounded-full ${styles.dot}`} />
                      <div>
                        <p className="font-semibold text-white">{item.topic}</p>
                        <p className="text-sm text-slate-400">{item.reason}</p>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em]">
                      <span className={`rounded-full px-3 py-1 ${actionStyles(item.action)}`}>{actionLabel(item.action)}</span>
                      <span className={`rounded-full px-3 py-1 ${styles.badge}`}>{item.urgency}</span>
                      <span className="rounded-full bg-white/10 px-3 py-1 text-slate-200">{item.estimatedMinutes} min</span>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-sm text-slate-400">No lower-urgency items are queued right now.</p>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
