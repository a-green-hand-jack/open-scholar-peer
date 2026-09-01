#!/usr/bin/env bash
# Open ScholarPeer — standalone OpenCode-native CLI installer

set -euo pipefail

REPOSITORY="${OSP_REPOSITORY:-a-green-hand-jack/open-scholar-peer}"
REF="${OSP_REF:-main}"
SCRIPT_SOURCE="${BASH_SOURCE[0]}"
SOURCE_DIR=""
TEMP_DIR=""

cleanup() {
  if [[ -n "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT

if [[ -f "$SCRIPT_SOURCE" ]]; then
  candidate_dir="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd)"
  if [[ -f "$candidate_dir/pyproject.toml" ]]; then
    SOURCE_DIR="$candidate_dir"
  fi
fi

if [[ -z "$SOURCE_DIR" ]]; then
  TEMP_DIR="$(mktemp -d)"
  SOURCE_DIR="$TEMP_DIR/open-scholar-peer"
  mkdir -p "$SOURCE_DIR"
  echo "Downloading ${REPOSITORY}@${REF}…"
  curl -fsSL "https://github.com/${REPOSITORY}/archive/${REF}.tar.gz" |
    tar -xz --strip-components=1 -C "$SOURCE_DIR"
fi

PYTHON="${PYTHON:-}"
python_is_supported() {
  "$1" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' >/dev/null 2>&1 &&
    "$1" -m pip --version >/dev/null 2>&1 &&
    "$1" -c 'import ensurepip, venv' >/dev/null 2>&1
}

if [[ -n "$PYTHON" ]] && ! python_is_supported "$PYTHON"; then
  echo "PYTHON must name Python 3.10+ with pip and venv support." >&2
  exit 1
fi

if [[ -z "$PYTHON" ]]; then
  for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && python_is_supported "$candidate"; then
      PYTHON="$candidate"
      break
    fi
  done
fi

if [[ -z "$PYTHON" ]]; then
  echo "No Python 3.10+ interpreter with pip and venv support was found. Install Python with pip and venv, then retry." >&2
  exit 1
fi

resolve_path() {
  "$PYTHON" -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).expanduser().resolve())' "$1"
}

INSTALL_DIR="$(resolve_path "${OSP_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/open-scholar-peer/cli}")"
BIN_DIR="$(resolve_path "${OSP_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}")"
mkdir -p "$BIN_DIR"
"$PYTHON" -m venv "$INSTALL_DIR"
"$INSTALL_DIR/bin/python" -m pip install --upgrade pip >/dev/null
"$INSTALL_DIR/bin/python" -m pip install "$SOURCE_DIR"
CLI_PATH="$INSTALL_DIR/bin/osp"
ln -sfn "$CLI_PATH" "$BIN_DIR/osp"
ln -sfn "$INSTALL_DIR/bin/open-scholar-peer" "$BIN_DIR/open-scholar-peer"
if ! "$CLI_PATH" doctor; then
  echo "The CLI was installed, but one or more runtime prerequisites are missing. Run '$CLI_PATH doctor' after installing them." >&2
fi

echo
echo "Open ScholarPeer CLI installed in:"
echo "  $INSTALL_DIR"
echo "Then start a review with:"
echo "  osp review ./paper.pdf --output ./osp-review --mode autonomous --headless"
echo
echo "If 'osp' is not found, add $BIN_DIR to PATH and open a new shell."
