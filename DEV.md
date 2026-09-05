# OSP Developer Verification

This repository uses a Docker-backed, user-like integration run instead of
unit tests. The image contains Node.js, OSP, OpenCode, Codex, Bohrium CLI,
Hugging Face CLI, Git and Poppler. Docker networking is enabled by default.

## Configure Access

The host configuration and authentication directories are mounted read-only
into the container. Do not copy credentials into the image or commit them:

```text
OpenCode config: ~/.config/opencode/opencode.jsonc
OpenCode auth:   ~/.local/share/opencode/auth.json
Codex config:    ~/.codex/config.toml
Codex auth:      ~/.codex/auth.json
Bohrium auth:    ~/.bohr
Hugging Face:    ~/.cache/huggingface
```

## Build

```bash
docker build -t open-scholar-peer:dev .
```

## Verify CLIs In The Container

These commands verify that the CLIs can read the mounted configuration and
authentication files. They do not print file contents.

```bash
docker run --rm \
  -v "$HOME/.config/opencode:/root/.config/opencode:ro" \
  -v "$HOME/.local/share/opencode:/root/.local/share/opencode:ro" \
  -v "$HOME/.codex:/root/.codex:ro" \
  -v "$HOME/.bohr:/root/.bohr:ro" \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface:ro" \
  --entrypoint bash open-scholar-peer:dev \
  -lc 'opencode --version && codex --version && bohr --version && hf version && bohr auth status && hf auth whoami'
```

## Run The Real OSP Review

Set `OSP_MODEL` to the same provider/model that works on the host. The default
Docker entrypoint runs all seven OSP phases, not `prepare-only`.

```bash
docker run --rm \
  -e OSP_MODEL=provider/model \
  -v "$HOME/.config/opencode:/root/.config/opencode:ro" \
  -v "$HOME/.local/share/opencode:/root/.local/share/opencode:ro" \
  -v "$HOME/.codex:/root/.codex:ro" \
  -v "$HOME/.bohr:/root/.bohr:ro" \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface:ro" \
  -v "$PWD/osp-docker-output:/tmp/osp-docker-output" \
  open-scholar-peer:dev
```

The output directory contains `final_review.md`, the run manifest, and the
isolated run workspace. To use another manuscript, mount it read-only and set
`OSP_DOCKER_SOURCE` to its container path. `OSP_NETWORK_POLICY` defaults to
`scholarly` and can be set to `online` or `offline`.

## Expected Result

The command must finish with `OSP Docker acceptance passed`. Inspect the
generated report and run:

```bash
osp validate <run-directory>
```

inside the container if a detailed validation report is needed. The default
`scholarly` network policy enables OSP academic providers; use
`OSP_NETWORK_POLICY=online` for generic web tools. A model-backed run requires
valid provider access and may consume model or literature API credits.

`bohr auth status` and `hf auth whoami` are intentionally run before the
review. The mounted Bohrium directory must contain a portable Bohrium login;
if it reports `logged_in: false`, pass the host's current Bohrium access key
without printing or storing it:

```bash
BOHR_ACCESS_KEY="$(bohr auth token)" docker run --rm \
  -e BOHR_ACCESS_KEY \
  -v "$HOME/.bohr:/root/.bohr:ro" \
  --entrypoint bash open-scholar-peer:dev \
  -lc 'bohr auth status'
```

The verified container output includes `ak_present: true` and
`logged_in: true`. The Hugging Face cache must contain the host login token.
