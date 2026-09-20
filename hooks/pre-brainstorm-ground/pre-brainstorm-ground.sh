#!/usr/bin/env bash
# pre-brainstorm-ground.sh — Tapway Superpowers fail-closed brainstorm grounding gate.
#
# Shared logic for all three harnesses (Claude Code / Codex / Hermes). Sources
# THIS file's sibling `pre-brainstorm-ground-lib.sh` when invoked standalone.
#
# Environment:
#   TAPWAY_BRAINSTORM_GATE=1  → enable (default: disabled — repo is public)
#   TAPWAY_SPECS_DIR          → platform specs repo checkout (default ~/platform-specs-local)
#   TAPWAY_PLATFORM           → platform name for the pack (default: from repo remote)
#
# Input (stdin JSON, harness-specific shapes):
#   Claude Code PreToolUse (Write/Edit): {"tool_input":{"file_path":"docs/brainstorming/x.md", ...}}
#   Codex:                                  {"file_path": "docs/brainstorming/x.md", ...}
#   Hermes pre_tool_call (terminal):        {"tool_input":{"command":"cat > docs/brainstorming/x.md ..."}}
#
# Output: {"decision":"block","reason":"..."} on violation, {} otherwise.
# Fail-closed ONLY when the gate is enabled: with the gate off, this hook is a
# no-op (the repo is public — we must not break external users' setups).

set -uo pipefail

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
[ -f "$LIB/pre-brainstorm-ground-lib.sh" ] || LIB="$(dirname "$0")"

payload="$(cat)"

# gate disabled → allow (public-repo safety default)
if [ "${TAPWAY_BRAINSTORM_GATE:-0}" != "1" ]; then
  printf '{}\n'
  exit 0
fi

# dispatch to the shared library
bash "$LIB/pre-brainstorm-ground-lib.sh" "$payload"
