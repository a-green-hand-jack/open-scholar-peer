#!/usr/bin/env bash
# Run Open ScholarPeer against the pinned Paper-Reviewing-Exam snapshot.
#
# The benchmark is never modified. OSP is installed inside the task container
# by the agent adapter, so nothing lands on the host.
#
#   ./harbor/run-osp.sh --install-only            # prove the install path, no spend
#   ./harbor/run-osp.sh de_novo_nanobody_discovery
#   ./harbor/run-osp.sh                           # the six-task benchmark set
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXAM_SHA="${EXAM_SHA:-67a17fe605e2190915d53cfbf397d8552503b007}"
OSP_REF="${OSP_REF:-main}"
MODEL="${MODEL:-openai/gpt-5.6-sol}"
JOBS_DIR="${JOBS_DIR:-$repo_root/../osp-harbor-jobs}"
JOB_NAME="${JOB_NAME:-osp-$(date -u +%Y%m%dT%H%M%SZ)}"
# OSP runs seven phases with three literature rounds, so it needs far more than
# the single-shot budget these tasks assume.
TIMEOUT_MULTIPLIER="${TIMEOUT_MULTIPLIER:-3.0}"

SIX_TASKS=(
  compression_induced_folding_of_a_sheet
  de_novo_nanobody_discovery
  hydrodynamics_of_large_language_models
  superconductivity_uniform_electron_gas
  transport_in_one_channel_luttinger_liquid
  trapping_centers_superfluid_mott_insulator
)

# Reached while Harbor builds the environment and the adapter installs Node,
# OpenCode and OSP. codeload is where the GitHub archive tarball redirects.
ENVIRONMENT_HOSTS=(
  archive.ubuntu.com security.ubuntu.com deb.debian.org
  github.com raw.githubusercontent.com objects.githubusercontent.com codeload.github.com
  nodejs.org registry.npmjs.org
)
# Reached by the review itself: the model provider plus the scholarly sources.
AGENT_HOSTS=(
  api.apexin.ai
  arxiv.org export.arxiv.org
  api.semanticscholar.org api.openalex.org api.crossref.org doi.org
  scholar.google.com
)

install_only=0
tasks=()
for arg in "$@"; do
  case "$arg" in
    --install-only) install_only=1 ;;
    *) tasks+=("$arg") ;;
  esac
done
((${#tasks[@]})) || tasks=("${SIX_TASKS[@]}")

# Credentials stay in the environment; nothing is written to the command line,
# the job record, or the task.
# Parsed rather than sourced: a stray space in `KEY = value` makes `.` execute
# the name as a command, and under `set -e` that kills the run before it starts.
if [[ -f "$repo_root/.env" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*)$ ]] || continue
    value="${BASH_REMATCH[2]}"
    value="${value%\"}"; value="${value#\"}"
    export "${BASH_REMATCH[1]}=$value"
  done < "$repo_root/.env"
fi
: "${OPENAI_BASE_URL:=${APEX_BASE_URL:-}}"
: "${OPENAI_API_KEY:=${APEX_API_KEY:-}}"
export OPENAI_BASE_URL OPENAI_API_KEY
[[ -n "$OPENAI_API_KEY" ]] || { echo "no model credential: set OPENAI_API_KEY or APEX_API_KEY" >&2; exit 1; }

args=(
  --repo "https://huggingface.co/datasets/Jack-Jieke-Wu/Paper-Reviewing-Exam/tree/$EXAM_SHA/paper-review-exam"
  --agent osp_harbor.agent:OpenScholarPeer
  --model "$MODEL"
  --ak "osp_ref=$OSP_REF"
  --ak network_policy=scholarly
  --ak qa_pairs=2
  --agent-timeout-multiplier "$TIMEOUT_MULTIPLIER"
  --jobs-dir "$JOBS_DIR"
  --job-name "$JOB_NAME"
  --n-concurrent 1 --n-concurrent-agents 1
  --no-delete --yes
  --artifact /workspace/material-manifest.json
)
((install_only)) && args+=(--install-only)
for t in "${tasks[@]}"; do args+=(--include-task-name "$t"); done
for h in "${ENVIRONMENT_HOSTS[@]}"; do args+=(--allow-environment-host "$h"); done
for h in "${AGENT_HOSTS[@]}"; do args+=(--allow-agent-host "$h"); done

echo "exam   : $EXAM_SHA"
echo "osp    : $OSP_REF"
echo "model  : $MODEL"
echo "tasks  : ${tasks[*]}"
echo "jobs   : $JOBS_DIR/$JOB_NAME"
((install_only)) && echo "mode   : install-only (no model spend)"

PYTHONPATH="$repo_root/harbor${PYTHONPATH:+:$PYTHONPATH}" exec harbor run "${args[@]}"
