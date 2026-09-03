import { z } from "zod";
import type { Phase } from "./phases.js";

export const PhaseStateSchema = z.object({
  status: z.enum(["pending", "running", "failed", "interrupted", "completed"]),
  attempts: z.number().int().nonnegative().default(0),
  started_at: z.string().nullable().default(null),
  completed_at: z.string().nullable().default(null),
  notes: z.string().default(""),
  error: z.string().nullable().default(null),
});

export const RunStateSchema = z.object({
  schema_version: z.literal("osp-run-v2"),
  run_id: z.string().min(1),
  status: z.enum(["preparing", "prepared", "running", "gate_waiting", "failed", "interrupted", "completed"]),
  mode: z.enum(["autonomous", "collaborative"]),
  phases: z.record(PhaseStateSchema),
  current_phase: z.string().nullable().default(null),
  scope: z.record(z.unknown()),
  scope_digest: z.string().length(64),
  provenance: z.record(z.unknown()).default({}),
  review_contract: z.object({ labels: z.array(z.string().min(1)).min(1), source: z.string().min(1), rationale: z.string().min(1) }).nullable().default(null),
  created_at: z.string(),
  updated_at: z.string(),
  completed_at: z.string().nullable().default(null),
  final_review: z.string().nullable().default(null),
});

export type RunState = z.infer<typeof RunStateSchema>;

export function initialPhases(): Record<Phase, z.infer<typeof PhaseStateSchema>> {
  return {
    onboarding: { status: "pending", attempts: 0, started_at: null, completed_at: null, notes: "", error: null },
    summary: { status: "pending", attempts: 0, started_at: null, completed_at: null, notes: "", error: null },
    literature: { status: "pending", attempts: 0, started_at: null, completed_at: null, notes: "", error: null },
    historian: { status: "pending", attempts: 0, started_at: null, completed_at: null, notes: "", error: null },
    baseline_scout: { status: "pending", attempts: 0, started_at: null, completed_at: null, notes: "", error: null },
    qa: { status: "pending", attempts: 0, started_at: null, completed_at: null, notes: "", error: null },
    review: { status: "pending", attempts: 0, started_at: null, completed_at: null, notes: "", error: null },
  };
}
