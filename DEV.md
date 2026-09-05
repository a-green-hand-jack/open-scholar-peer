# OSP Developer Verification

This repository uses a Docker-backed, user-like integration run instead of
unit tests. The image contains Node.js, OSP, OpenCode, Codex, Git and Poppler.

## Configure Access

The host configuration files are mounted read-only into the container. Do not
copy them into the image or commit them:

```text
OpenCode config: ~/.config/opencode/opencode.jsonc
OpenCode auth:   ~/.local/share/opencode/auth.json
Codex config:    ~/.codex/config.toml
Codex auth:      ~/.codex/auth.json
```

## Build

```bash
docker build -t open-scholar-peer:dev .
```

## Verify CLIs In The Container

These commands verify that both CLIs can read the mounted configuration and
authentication files. They do not print file contents.

```bash
docker run --rm \
  -v "$HOME/.config/opencode:/root/.config/opencode:ro" \
  -v "$HOME/.local/share/opencode:/root/.local/share/opencode:ro" \
  -v "$HOME/.codex:/root/.codex:ro" \
  --entrypoint bash open-scholar-peer:dev \
  -lc 'opencode --version && codex --version'
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

inside the container if a detailed validation report is needed. A model-backed
run requires valid provider access and may consume model or literature API
credits.
