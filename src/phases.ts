export const PHASES = [
  "onboarding",
  "summary",
  "literature",
  "historian",
  "baseline_scout",
  "qa",
  "review",
] as const;

export type Phase = (typeof PHASES)[number];

export const COMMANDS: Record<Phase, string> = {
  onboarding: "0-osp-onboarding",
  summary: "1-osp-summary",
  literature: "2-osp-literature",
  historian: "3-osp-historian",
  baseline_scout: "4-osp-baseline-scout",
  qa: "5-osp-qa",
  review: "6-osp-review",
};

export const FIXED_OUTPUTS: Record<Phase, readonly string[]> = {
  onboarding: [".brain/raw/00_review_guidelines.md"],
  summary: [".brain/raw/01_structured_summary.md"],
  literature: [
    ".brain/raw/02a_literature_round1.md",
    ".brain/raw/02b_literature_round2.md",
    ".brain/raw/02c_literature_round3.md",
    ".brain/raw/02_retrieved_literature.md",
  ],
  historian: [".brain/raw/03_domain_narrative.md"],
  baseline_scout: [".brain/raw/04_missing_baselines.md"],
  qa: [],
  review: [".brain/review/final_review.md"],
};

export const LITERATURE_STRATEGIES = [
  "sub-domain-anchor",
  "method-anchor",
  "temporal-expansion",
] as const;

/**
 * Artifact paths a phase is contracted to write. Q&A expands to one file per
 * onboarding-declared criterion.
 */
export function expectedOutputs(session: unknown, phase: Phase): string[] {
  if (phase !== "qa") return [...FIXED_OUTPUTS[phase]];
  const criteria = (session as { qa_criteria?: Array<{ slug?: string }> } | null)?.qa_criteria ?? [];
  return criteria.filter((criterion) => criterion.slug).map((criterion) => `.brain/raw/05_qa_${criterion.slug}.md`);
}
