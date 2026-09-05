#!/usr/bin/env bash
set -euo pipefail
output="${OSP_DOCKER_OUTPUT:-/tmp/osp-docker-output}"
source="${OSP_DOCKER_SOURCE:-/workspace/docs/paper/scholar_peer_arxiv.pdf}"
: "${OSP_MODEL:?Set OSP_MODEL to a configured provider/model before running the container}"
mkdir -p "$output"
for entry in "$output"/* "$output"/.[!.]*; do
  [[ -e "$entry" ]] || continue
  rm -rf "$entry"
done
node dist/cli.js doctor
bohr auth status
hf auth whoami
review_args=(review "$source" --output "$output" --network-policy "${OSP_NETWORK_POLICY:-scholarly}" \
  --headless --mode autonomous --model "$OSP_MODEL" --final-output "$output/final_review.md")
if [[ "${OSP_ALLOW_LKM_SPEND:-false}" == "true" ]]; then review_args+=(--allow-lkm-spend); fi
node dist/cli.js "${review_args[@]}"
run_dir="$(find "$output" -mindepth 1 -maxdepth 1 -type d -name 'osp-*' -print -quit)"
[[ -n "$run_dir" ]]
node dist/cli.js status "$run_dir" --json >/dev/null
node dist/cli.js validate "$run_dir" --json
[[ -s "$output/final_review.md" ]]
[[ -f "$run_dir/.brain/review/final_review.md" ]]
[[ -f "$run_dir/.osp-run/run.json" && -f "$run_dir/.osp-run/source-manifest.json" ]]
[[ -f "$run_dir/.git/HEAD" ]]
echo "OSP Docker acceptance passed: $run_dir"
