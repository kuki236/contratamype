import { geminiIntro } from "./gemini";
import { templateExplainer, type Explanation } from "./explainer";
import type { OpportunityDetail } from "./types";

export async function explainOpportunity(detail: OpportunityDetail): Promise<Explanation> {
  const template = templateExplainer(detail);
  if (process.env.CONTRATAMYPE_EXPLAINER?.trim().toLowerCase() !== "gemini") return template;
  const intro = await geminiIntro(detail);
  return intro ? { ...template, intro, provider: "gemini" } : template;
}
