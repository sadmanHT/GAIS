const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface DiagnosticsResponse {
  status: string;
  version: string;
  models_loaded: boolean;
}

export interface SubmitAnswerRequest {
  user_id: string;
  question_id: number;
  correct: boolean;
  response_time_ms: number;
  confidence_score: number;
}

export interface SubmitAnswerResponse {
  user_id: string;
  question_id: number;
  engagement_score: number;
  confusion_score: number;
  retention_score: number;
  mastery_probability: number;
}

export interface NextQuestionResponse {
  question_id: number;
  content: string;
  topic: string;
  difficulty: "easy" | "medium" | "hard" | string;
  hint: string;
}

export interface ConceptProgress {
  concept: string;
  mastery_probability: number;
}

export interface UserProgressResponse {
  user_id: string;
  concepts: ConceptProgress[];
  weakest_concepts: ConceptProgress[];
  overall_accuracy: number;
  total_questions_answered: number;
}

export interface StudyPlanItem {
  topic: string;
  action: "revise" | "practice new";
  reason: string;
  urgency: "high" | "medium" | "low";
}

export interface RecommendationResponse {
  user_id: string;
  study_plan: StudyPlanItem[];
}

export interface DiagnosticFinding {
  title: string;
  detail: string;
  severity: "high" | "medium" | "low" | string;
}

export interface DiagnosticInsightResponse {
  user_id: string;
  summary: string;
  findings: DiagnosticFinding[];
}

export interface MockTestQuestion {
  question_id: number;
  content: string;
  topic: string;
  difficulty: string;
}

export interface MockTestSection {
  title: string;
  duration_minutes: number;
  questions: MockTestQuestion[];
}

export interface MockTestResponse {
  user_id: string;
  sections: MockTestSection[];
}

export interface UserSettingsResponse {
  user_id: string;
  time_pressure: boolean;
  audio_cues: boolean;
  daily_session_minutes: number;
  weekly_summary: boolean;
  target_score: number | null;
  test_date: string | null;
  weakest_area: string | null;
}

export type UserSettingsUpdate = Partial<Omit<UserSettingsResponse, "user_id">>;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `Request failed with status ${response.status}`;
    throw new Error(detail);
  }

  return body as T;
}

export async function submitAnswer(
  userId: string,
  questionId: number,
  correct: boolean,
  responseTimeMs: number,
  confidenceScore: number,
) {
  const payload: SubmitAnswerRequest = {
    user_id: userId,
    question_id: questionId,
    correct,
    response_time_ms: responseTimeMs,
    confidence_score: confidenceScore,
  };

  return request<SubmitAnswerResponse>("/submit-answer", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getNextQuestion(userId: string) {
  const params = new URLSearchParams({ user_id: userId });
  return request<NextQuestionResponse>(`/next-question?${params.toString()}`);
}

export async function getUserProgress(userId: string) {
  const params = new URLSearchParams({ user_id: userId });
  return request<UserProgressResponse>(`/user-progress?${params.toString()}`);
}

export async function getRecommendation(userId: string) {
  const params = new URLSearchParams({ user_id: userId });
  return request<RecommendationResponse>(`/recommendation?${params.toString()}`);
}

export async function getPlan(userId: string) {
  const params = new URLSearchParams({ user_id: userId });
  return request<RecommendationResponse>(`/plan?${params.toString()}`);
}

export async function getDiagnostic(userId: string) {
  const params = new URLSearchParams({ user_id: userId });
  return request<DiagnosticInsightResponse>(`/diagnostic?${params.toString()}`);
}

export async function getMockTest(userId: string) {
  const params = new URLSearchParams({ user_id: userId });
  return request<MockTestResponse>(`/mock-test?${params.toString()}`);
}

export async function getSettings(userId: string) {
  const params = new URLSearchParams({ user_id: userId });
  return request<UserSettingsResponse>(`/settings?${params.toString()}`);
}

export async function updateSettings(userId: string, settings: UserSettingsUpdate) {
  const params = new URLSearchParams({ user_id: userId });
  return request<UserSettingsResponse>(`/settings?${params.toString()}`, {
    method: "PUT",
    body: JSON.stringify(settings),
  });
}

export async function submitOnboarding(userId: string, settings: UserSettingsUpdate) {
  const params = new URLSearchParams({ user_id: userId });
  return request<UserSettingsResponse>(`/onboarding?${params.toString()}`, {
    method: "POST",
    body: JSON.stringify(settings),
  });
}

export async function getDiagnostics() {
  return request<DiagnosticsResponse>("/diagnostics");
}
