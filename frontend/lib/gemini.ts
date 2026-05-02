import { GoogleGenerativeAI } from "@google/generative-ai";

export interface GeneratedQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

const apiKey = process.env.NEXT_PUBLIC_GEMINI_API_KEY;
const genAI = apiKey ? new GoogleGenerativeAI(apiKey) : null;

function getModel() {
  if (!genAI) {
    throw new Error("NEXT_PUBLIC_GEMINI_API_KEY is not configured.");
  }
  return genAI.getGenerativeModel({ model: "gemini-pro" });
}

function extractJson(text: string) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const candidate = fenced?.[1] ?? text;
  const firstBrace = candidate.indexOf("{");
  const lastBrace = candidate.lastIndexOf("}");
  if (firstBrace === -1 || lastBrace === -1 || lastBrace <= firstBrace) {
    throw new Error("Gemini response did not contain a JSON object.");
  }
  return JSON.parse(candidate.slice(firstBrace, lastBrace + 1));
}

function normalizeQuestion(value: unknown): GeneratedQuestion {
  const raw = value as Partial<GeneratedQuestion>;
  if (
    typeof raw.question !== "string" ||
    !Array.isArray(raw.options) ||
    raw.options.length !== 4 ||
    typeof raw.correct_index !== "number" ||
    typeof raw.explanation !== "string"
  ) {
    throw new Error("Gemini question JSON did not match the expected shape.");
  }

  return {
    question: raw.question,
    options: raw.options.map(String),
    correct_index: Math.min(Math.max(Math.round(raw.correct_index), 0), 3),
    explanation: raw.explanation,
  };
}

async function generateText(prompt: string) {
  const model = getModel();
  const result = await model.generateContent(prompt);
  return result.response.text().trim();
}

export async function generateQuestion(
  topic: string,
  difficulty: string,
  previousQuestionIds: Array<string | number> = [],
): Promise<GeneratedQuestion> {
  try {
    const text = await generateText(`
Generate a unique GRE-style multiple choice question.

Topic: ${topic}
Difficulty: ${difficulty}
Avoid repeating these previous question IDs or themes: ${previousQuestionIds.join(", ") || "none"}

Return only JSON with this exact shape:
{
  "question": "string",
  "options": ["string", "string", "string", "string"],
  "correct_index": 0,
  "explanation": "string"
}
`);
    return normalizeQuestion(extractJson(text));
  } catch (error) {
    console.error("generateQuestion failed:", error);
    return {
      question: `Practice ${topic} question (${difficulty})`,
      options: ["Option A", "Option B", "Option C", "Option D"],
      correct_index: 0,
      explanation: "Gemini was unavailable, so a placeholder question was used.",
    };
  }
}

export async function generateHint(question: string, userAnswer: string, correctAnswer: string) {
  try {
    return await generateText(`
Give a 2-sentence Socratic hint without revealing the answer.

Question: ${question}
User answer: ${userAnswer}
Correct answer: ${correctAnswer}
`);
  } catch (error) {
    console.error("generateHint failed:", error);
    return "Think about which principle the question is testing. What evidence in the prompt rules out your first choice?";
  }
}

export async function generateDiagnostic(weakTopics: string[], recentMistakes: string[]) {
  try {
    return await generateText(`
Write a 3-sentence personalized study insight.

Weak topics: ${weakTopics.join(", ") || "none"}
Recent mistakes: ${recentMistakes.join("; ") || "none"}
`);
  } catch (error) {
    console.error("generateDiagnostic failed:", error);
    return "Your recent work shows a few patterns worth reviewing. Focus first on the weakest topics, then retry similar questions slowly. Keep sessions short and deliberate so mistakes become feedback instead of noise.";
  }
}

export async function generateMotivation(accuracy: number, streak: number, username: string) {
  try {
    return await generateText(`
Write one short encouraging message for ${username}.
Current accuracy: ${Math.round(accuracy * 100)}%
Current correct streak: ${streak}
Keep it specific, warm, and under 25 words.
`);
  } catch (error) {
    console.error("generateMotivation failed:", error);
    return `${username}, keep going. Every answer is giving the system a clearer map of what to practice next.`;
  }
}
