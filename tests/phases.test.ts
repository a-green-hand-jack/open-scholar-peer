import { describe, expect, it } from "vitest";
import { FIXED_OUTPUTS, LITERATURE_STRATEGIES, PHASES } from "../src/phases.js";
import { initialPhases, RunStateSchema } from "../src/state.js";

describe("OSP protocol registry", () => {
  it("keeps the ScholarPeer seven-stage order", () => {
    expect(PHASES).toEqual(["onboarding", "summary", "literature", "historian", "baseline_scout", "qa", "review"]);
  });

  it("keeps three auditable literature rounds", () => {
    expect(LITERATURE_STRATEGIES).toEqual(["sub-domain-anchor", "method-anchor", "temporal-expansion"]);
    expect(FIXED_OUTPUTS.literature).toHaveLength(4);
  });

  it("creates schema-valid pending phase state", () => {
    const scope = { workflow: [...PHASES] };
    expect(() => RunStateSchema.parse({
      schema_version: "osp-run-v2", run_id: "test", status: "prepared", mode: "autonomous",
      phases: initialPhases(), current_phase: null, scope, scope_digest: "a".repeat(64),
      created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z", completed_at: null, final_review: null,
    })).not.toThrow();
  });
});
