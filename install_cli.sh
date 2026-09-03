#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="${OSP_REPOSITORY:-a-green-hand-jack/open-scholar-peer}"
REF="${OSP_REF:-main}"
SOURCE_DIR=""
TEMP_DIR=""
cleanup() { [[ -z "$TEMP_DIR" ]] || rm -rf "$TEMP_DIR"; }
trap cleanup EXIT

SCRIPT_SOURCE="${BASH_SOURCE[0]:-}"
SCRIPT_DIR=""
if [[ -n "$SCRIPT_SOURCE" && -f "$SCRIPT_SOURCE" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd)"
fi
if [[ -n "${OSP_SOURCE_DIR:-}" ]]; then
  SOURCE_DIR="$(cd "$OSP_SOURCE_DIR" && pwd)"
elif [[ -n "$SCRIPT_DIR" && -f "$SCRIPT_DIR/package.json" ]]; then
  SOURCE_DIR="$SCRIPT_DIR"
else
  TEMP_DIR="$(mktemp -d)"
  SOURCE_DIR="$TEMP_DIR/open-scholar-peer"
  mkdir -p "$SOURCE_DIR"
  curl -fsSL "https://github.com/${REPOSITORY}/archive/${REF}.tar.gz" | tar -xz --strip-components=1 -C "$SOURCE_DIR"
fi

NODE="${NODE:-node}"
NPM="${NPM:-npm}"
command -v "$NODE" >/dev/null || { echo "Node.js >= 20 is required." >&2; exit 1; }
NODE_MAJOR="$("$NODE" -p 'process.versions.node.split(".")[0]')"
(( NODE_MAJOR >= 20 )) || { echo "Node.js >= 20 is required." >&2; exit 1; }

INSTALL_DIR="${OSP_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/open-scholar-peer}"
BIN_DIR="${OSP_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}"
mkdir -p "$INSTALL_DIR" "$BIN_DIR"
if [[ "$SOURCE_DIR" != "$INSTALL_DIR/source" ]]; then
  rm -rf "$INSTALL_DIR/source"
  cp -R "$SOURCE_DIR" "$INSTALL_DIR/source"
fi
cd "$INSTALL_DIR/source"
"$NPM" install
"$NPM" run build
chmod +x "$INSTALL_DIR/source/dist/cli.js"
install_link() {
  local target="$1" link="$2"
  if [[ -e "$link" || -L "$link" ]]; then
    if [[ ! -L "$link" || "$(readlink -f "$link")" != "$target" ]]; then
      echo "Refusing to overwrite existing executable: $link" >&2
      exit 1
    fi
  else
    ln -s "$target" "$link"
  fi
}
install_link "$INSTALL_DIR/source/dist/cli.js" "$BIN_DIR/osp"
install_link "$INSTALL_DIR/source/dist/cli.js" "$BIN_DIR/open-scholar-peer"
echo "Open ScholarPeer installed at $INSTALL_DIR"
echo "Add $BIN_DIR to PATH, then run: osp doctor"
