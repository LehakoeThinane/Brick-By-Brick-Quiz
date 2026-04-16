const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type QuizMode = "category" | "adaptive" | "review";

export type MasterySignal = string;
export type MasteryState = string;

export type Option = { key: string; text: string };

export type JsonObject = Record<string, unknown>;

export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  path: string,
  {
    method,
    token,
    body,
  }: { method?: string; token?: string | null; body?: unknown } = {},
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: method ?? (body ? "POST" : "GET"),
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail: string | undefined;
    try {
      const data = (await res.json()) as { detail?: string };
      detail = data?.detail;
    } catch {
      // ignore
    }
    throw new ApiError(`Request failed (${res.status})`, res.status, detail);
  }

  return (await res.json()) as T;
}

// Auth
export async function login(tokenPayload: { email: string; password: string }) {
  const data = await request<{ access_token: string }>(`/auth/login`, {
    method: "POST",
    body: tokenPayload,
  });
  return data.access_token;
}

export async function register(payload: {
  email: string;
  password: string;
  display_name?: string;
}) {
  const data = await request<{ access_token: string }>(`/auth/register`, {
    method: "POST",
    body: payload,
  });
  return data.access_token;
}

// Dashboard
export async function getMyProgress(token: string) {
  return request<{
    user_id: string;
    struggling_topics: number;
    developing_topics: number;
    mastered_topics: number;
    topics: Array<{
      category_id: string;
      category_name: string;
      mastery_state: MasteryState;
      total_attempts: number;
      correct_count: number;
      rolling_accuracy: number | null;
      avg_response_time_ms: number | null;
      consecutive_correct: number;
      last_attempted_at: string | null;
    }>;
  }>(`/users/me/progress`, { token, method: "GET" });
}

export async function getReviewQueueSummary(token: string) {
  return request<{
    total_items: number;
    pending_items: number;
    top_priority_score: number | null;
  }>(`/review-queue/summary`, { token, method: "GET" });
}

export async function createSession(token: string, payload: {
  mode: QuizMode;
  category_id?: string | null;
  total_questions?: number;
}) {
  return request<{
    session_id: string;
    mode: QuizMode;
    status: string;
    total_questions: number;
    expires_at: string;
  }>(`/sessions`, { token, method: "POST", body: payload });
}

// Quiz
export async function getNextQuestion(token: string, sessionId: string) {
  return request<{
    session_id: string;
    question_number: number;
    total_questions: number;
    question: {
      id: string;
      version: number;
      category_id: string | null;
      subcategory: string | null;
      tags: string[] | null;
      difficulty: number | null;
      question_type: string | null;
      question_text: string;
      options: Option[] | Record<string, unknown>;
      hint: string | null;
    };
  }>(`/sessions/${sessionId}/next`, { token, method: "GET" });
}

export async function submitAnswer(
  token: string,
  sessionId: string,
  payload: {
    question_id: string;
    question_version: number;
    submitted_answer: string;
    response_time_ms: number;
  },
) {
  return request<{
    question_id: string;
    is_correct: boolean;
    correct_answer: string;
    explanation: string;
    mastery_signal: MasterySignal;
    response_time_ms: number;
  }>(`/sessions/${sessionId}/answer`, {
    token,
    method: "POST",
    body: payload,
  });
}

export async function getSessionResults(token: string, sessionId: string) {
  return request<{
    session_id: string;
    total_questions: number;
    correct_count: number;
    accuracy_percent: number;
    weak_topics: string[];
    average_response_time_ms: number | null;
    total_time_ms: number | null;
  }>(`/sessions/${sessionId}/results`, { token, method: "GET" });
}

// Review
export async function getReviewQueue(token: string) {
  return request<
    Array<{
      id: string;
      question_id: string;
      question_version: number;
      category_id: string | null;
      subcategory: string | null;
      tags: string[] | null;
      difficulty: number | null;
      question_type: string | null;
      question_text: string;
      options: Option[] | Record<string, unknown>;
      hint: string | null;
      correct_answer: string;
      explanation: string;
      priority_score: number;
      reason: string | null;
      added_at: string;
      reviewed_at: string | null;
    }>
  >(`/review-queue`, { token, method: "GET" });
}

export async function answerReviewQueueItem(
  token: string,
  itemId: string,
  payload: { submitted_answer: string; response_time_ms: number },
) {
  return request<{
    item_id: string;
    is_correct: boolean;
    updated_priority_score: number;
    reviewed: boolean;
  }>(`/review-queue/${itemId}/answer`, {
    token,
    method: "POST",
    body: payload,
  });
}

