export const NETWORK_POLICIES = ["scholarly", "online", "offline"] as const;

export type NetworkPolicy = (typeof NETWORK_POLICIES)[number];

/**
 * Scholarly mode is deliberately narrower than generic online access. The OSP
 * MCP exposes only the benchmark-approved scholarly providers; OpenCode's
 * unrestricted web tools stay disabled.
 */
export function allowsMcp(policy: NetworkPolicy): boolean {
  return policy !== "offline";
}

export function allowsOpenCodeWeb(policy: NetworkPolicy): boolean {
  return policy === "online";
}
