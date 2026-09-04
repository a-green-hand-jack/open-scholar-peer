"""Harbor agent that runs Open ScholarPeer as itself.

Harbor invokes the released `osp` CLI inside the task container. The controller
that ships with that release owns the review: phase ordering, artifact
validation, write verification, checkpointing, and the recommendation contract
all run for real. Nothing here reimplements or stands in for any of it, so a
benchmark result is attributable to OSP rather than to a prompt handed to a
generic coding agent.
"""

from __future__ import annotations

import json
import os
import shlex
from typing import Any, override

from harbor.agents.installed.base import BaseInstalledAgent
from harbor.agents.installed.node_install import nvm_node_install_snippet
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

# The task image ships Node 18 (Ubuntu 24.04); OSP requires 20+, so nvm is not
# optional here. Every later command re-sources it because each exec is a fresh
# shell.
NODE_MAJOR = 22
PRELUDE = (
    '. "$HOME/.nvm/nvm.sh" >/dev/null 2>&1 || true; '
    'export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"; '
)

# Mirrors the provider/env mapping Harbor's own OpenCode adapter uses, so an
# OpenAI-compatible endpoint is reached with OPENAI_BASE_URL + OPENAI_API_KEY
# and no provider file has to be written into the container.
PROVIDER_ENV: dict[str, list[str]] = {
    "anthropic": ["ANTHROPIC_API_KEY"],
    "openai": ["OPENAI_API_KEY", "OPENAI_BASE_URL"],
    "openrouter": ["OPENROUTER_API_KEY"],
    "google": ["GEMINI_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
    "xai": ["XAI_API_KEY"],
    "opencode": ["OPENCODE_API_KEY"],
}

# Passed through to the review when present in the launch environment.
RETRIEVAL_ENV = ["SEMANTIC_SCHOLAR_API_KEY", "OSP_CALL_TIMEOUT"]


def _as_bool(value: Any) -> bool:
    """Harbor delivers --ak values as strings, so "false" must not read true."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class OpenScholarPeer(BaseInstalledAgent):
    """Runs `osp review` on the task manuscript and exports the submission."""

    SUPPORTS_RESUME: bool = False

    def __init__(
        self,
        *args: Any,
        osp_ref: str = "main",
        osp_repository: str = "a-green-hand-jack/open-scholar-peer",
        opencode_version: str = "1.18.25",
        network_policy: str = "scholarly",
        qa_pairs: int | str = 2,
        allow_lkm_spend: bool | str = False,
        variant: str | None = None,
        mode: str = "autonomous",
        opencode_config: dict[str, Any] | str | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._osp_ref = osp_ref
        self._osp_repository = osp_repository
        self._opencode_version = opencode_version
        self._network_policy = network_policy
        self._qa_pairs = int(qa_pairs)
        self._allow_lkm_spend = _as_bool(allow_lkm_spend)
        self._variant = variant
        self._mode = mode
        if isinstance(opencode_config, str):
            opencode_config = json.loads(opencode_config)
        self._opencode_config: dict[str, Any] | None = opencode_config

    @staticmethod
    @override
    def name() -> str:
        return "open-scholar-peer"

    @override
    def get_version_command(self) -> str | None:
        return f"{PRELUDE} osp --version"

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        # The exam image already carries these and keeps its apt lists, so this
        # is a no-op there rather than a network call.
        await self.exec_as_root(
            environment,
            command="apt-get install -y --no-install-recommends curl git poppler-utils ca-certificates",
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; "
                f"{nvm_node_install_snippet(NODE_MAJOR)} && "
                f"npm i -g opencode-ai@{self._opencode_version} && opencode --version"
            ),
            timeout_sec=900,
        )
        if self._opencode_config is not None:
            await self._write_opencode_config(environment)
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; "
                f'. "$HOME/.nvm/nvm.sh" && '
                f"export OSP_REPOSITORY={shlex.quote(self._osp_repository)} && "
                f"export OSP_REF={shlex.quote(self._osp_ref)} && "
                "curl -fsSL "
                f'"https://raw.githubusercontent.com/{self._osp_repository}/{self._osp_ref}/install_cli.sh" | bash'
            ),
            timeout_sec=1800,
        )
        # doctor is the install gate: it fails loudly here rather than letting a
        # missing dependency surface as an unexplained phase error mid-review.
        await self.exec_as_agent(environment, command=f"set -euo pipefail; {PRELUDE} osp doctor")

    async def _write_opencode_config(self, environment: BaseEnvironment) -> None:
        """Install a global opencode.json for providers OpenCode cannot infer."""
        payload = shlex.quote(json.dumps(self._opencode_config, indent=2))
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; mkdir -p \"$HOME/.config/opencode\" && "
                f'printf %s {payload} > "$HOME/.config/opencode/opencode.json"'
            ),
        )

    def _provider_env(self) -> dict[str, str]:
        env: dict[str, str] = {}
        provider = (self.model_name or "").split("/", 1)[0]
        for key in PROVIDER_ENV.get(provider, []) + RETRIEVAL_ENV:
            if key in os.environ:
                env[key] = os.environ[key]
        return env

    @override
    def populate_context_post_run(self, context: AgentContext) -> None:
        pass

    @override
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        # The task instruction is not forwarded as a prompt: OSP runs its own
        # seven-phase protocol and reads /workspace/paper itself. It is written
        # to the log so a trail records what the task asked for.
        if not self.model_name:
            raise ValueError("open-scholar-peer requires --model provider/model")

        review = [
            "osp review /workspace/paper",
            "--output /workspace/osp-review",
            "--final-output /workspace/submission/review.md",
            "--trail /workspace/submission/osp-trail",
            "--headless",
            f"--mode {shlex.quote(self._mode)}",
            f"--network-policy {shlex.quote(self._network_policy)}",
            f"--qa-pairs {self._qa_pairs}",
            f"--model {shlex.quote(self.model_name)}",
        ]
        if self._variant:
            review.append(f"--variant {shlex.quote(self._variant)}")
        if self._allow_lkm_spend:
            review.append("--allow-lkm-spend")

        command = (
            "set -o pipefail; "
            f"{PRELUDE}"
            "mkdir -p /workspace/submission /logs/agent && "
            f"printf %s {shlex.quote(instruction)} > /logs/agent/task-instruction.md; "
            f"{' '.join(review)} 2>&1 | tee /logs/agent/osp-review.log; "
            "status=${PIPESTATUS[0]}; "
            # Validation output is the most useful triage artifact when a run
            # finishes but the review is malformed, so collect it either way.
            "osp validate /workspace/osp-review --json > /logs/agent/osp-validate.json 2>&1 || true; "
            "cp /workspace/osp-review/run-manifest.json /logs/agent/ 2>/dev/null || true; "
            "exit $status"
        )
        await self.exec_as_agent(environment, command=command, env=self._provider_env())
