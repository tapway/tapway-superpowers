#!/usr/bin/env bash
# Hermes shell hook — pre_tool_call blocker for ungrounded brainstorm-doc writes.
# Receives JSON on stdin: {"tool_name":"terminal","tool_input":{"command":"..."}}
# or {"tool_name":"write", ...}. Returns {"decision":"block","reason":"..."} to veto.
#
# Shared logic lives in pre-brainstorm-ground-lib.sh (sibling file).
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

payload="$(cat)"

# gate disabled → allow (public-repo safety default)
if [ "${TAPWAY_BRAINSTORM_GATE:-0}" != "1" ]; then
  printf '{}\n'
  exit 0
fi

# dispatch to the shared library
bash "$LIB/pre-brainstorm-ground-lib.sh" "$payload"
