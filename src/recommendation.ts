const DECISION_LABELS = ["accept", "weak accept", "borderline", "weak reject", "reject"];
const READINESS_LABELS = ["ready", "ready with minor revisions", "needs revision", "needs major revision", "not ready"];

export type RecommendationContract = {
  labels: string[];
  source: string;
  rationale: string;
  valid: boolean;
};

function record(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? value as Record<string, unknown> : {};
}

function labelsFromGuidelines(guidelines?: string): string[] {
  const output = guidelines?.split(/^## Output\s*$/m)[1]?.split(/^## /m)[0] ?? "";
  const line = output.split("\n").find((candidate) => /decision recommendation/i.test(candidate) && /[—–:]/.test(candidate));
  if (!line) return [];
  const value = line.split(/[—–:]/).at(-1)?.replace(/\*+/g, "").split(/,\s+(?:with|followed by)\b/i)[0] ?? "";
  return value.split(/\s*(?:\/|·|;|\||,)\s*/).map((label) => label.trim()).filter((label) => label.length > 0 && label.length <= 96 && !/[\r\n]/.test(label));
}

export function recommendationContract(session: unknown, guidelines?: string): RecommendationContract {
  const sessionRecord = record(session);
  const hasConfiguration = Boolean(sessionRecord.recommendation && typeof sessionRecord.recommendation === "object");
  const configured = record(sessionRecord.recommendation);
  const labels = Array.isArray(configured.labels)
    ? configured.labels.filter((label): label is string => typeof label === "string" && label.trim().length > 0).map((label) => label.trim())
    : [];
  const rationale = typeof configured.rationale === "string" ? configured.rationale.trim() : "";
  const source = typeof configured.source === "string" ? configured.source.trim() : "";
  if (hasConfiguration) {
    const sameLabels = (expected: string[]) => labels.length === expected.length && labels.every((label, index) => label === expected[index]);
    const valid = labels.length > 0 && new Set(labels).size === labels.length && rationale.length > 0
      && (source === "venue" || (source === "publication-decision fallback" && sameLabels(DECISION_LABELS)) || (source === "preprint fallback" && sameLabels(READINESS_LABELS)));
    return { labels, source: source || "pending", rationale, valid };
  }

  const venue = record(sessionRecord.venue);
  const nonDecision = typeof venue.name === "string" && /(?:\bpreprint\b|\b\w*rxiv\b)/i.test(venue.name);
  const criteriaSource = typeof venue.criteria_source === "string" ? venue.criteria_source : "";

  const legacyLabels = labelsFromGuidelines(guidelines);
  if ((criteriaSource === "web" || criteriaSource === "user") && legacyLabels.length > 0) return { labels: legacyLabels, source: "saved venue guidelines", rationale: "The saved venue guidelines define this recommendation vocabulary.", valid: true };
  if (nonDecision) return { labels: READINESS_LABELS, source: "preprint fallback", rationale: "This venue makes no publication decision, so this is a readiness judgement.", valid: true };
  if (legacyLabels.length > 0) return { labels: legacyLabels, source: "saved venue guidelines", rationale: "The saved venue guidelines define this recommendation vocabulary.", valid: true };
  return { labels: DECISION_LABELS, source: "publication-decision fallback", rationale: "This venue makes publication decisions, so this is a decision judgement.", valid: true };
}

export function recommendationFormat(contract: RecommendationContract): string {
  return `one controlled label from ${contract.source}: ${contract.labels.map((label) => `\`${label}\``).join(", ")}`;
}
