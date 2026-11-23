import type { OpportunityDetail } from "./types";

const FORBIDDEN = /\b(elegible|elegibilidad|puede postular|califica|cumple los requisitos)\b/i;

interface GeminiResponse {
  candidates?: Array<{
    content?: { parts?: Array<{ text?: string }> };
  }>;
}

function officialFields(detail: OpportunityDetail): Record<string, unknown> {
  return {
    ocid: detail.ocid,
    title: detail.title,
    description: detail.description,
    category: detail.category,
    method: detail.method,
    amount_pen: detail.amount_pen,
    currency: detail.currency,
    published_date: detail.published_date,
    tender_start: detail.tender_start,
    tender_end: detail.tender_end,
    buyer: detail.buyer?.name ?? detail.buyer_name,
    department: detail.department,
    data_quality: detail.data_quality,
  };
}

export async function geminiIntro(detail: OpportunityDetail): Promise<string | null> {
  const key = process.env.GEMINI_API_KEY?.trim();
  if (!key) return null;
  const model = process.env.GEMINI_MODEL?.trim() || "gemini-3.5-flash";
  const prompt = [
    "Redacta 2 o 3 frases en español claro para una MYPE sobre este proceso de compras públicas.",
    "Usa solo los campos oficiales del JSON. No inventes requisitos, documentos, fechas ni montos.",
    "No afirmes elegibilidad legal ni que la empresa 'puede postular'. No des asesoría legal.",
    "No repitas el disclaimer; se agrega aparte.",
    `Datos oficiales: ${JSON.stringify(officialFields(detail))}`,
  ].join("\n");

  try {
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          contents: [{ role: "user", parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.2, maxOutputTokens: 220 },
        }),
        signal: AbortSignal.timeout(5000),
      },
    );
    if (!response.ok) return null;
    const payload = (await response.json()) as GeminiResponse;
    const text = payload.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
    if (!text || text.length > 800 || FORBIDDEN.test(text)) return null;
    return text;
  } catch {
    return null;
  }
}
