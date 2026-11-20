#!/bin/bash
# Write an env file whose secrets are canaries, for skill evals.
#
#   canary-env.sh <file> KEY [KEY ...] [NAME=value ...]
#
# A bare KEY becomes KEY=CANARY-<key>-<6 hex>; NAME=value is written as is
# (non-secret settings the skill needs). Any CANARY- string in an eval
# transcript means a secret reached the model. Prints the file name only,
# never a value.
set -eu
if [ $# -lt 2 ]; then
  echo "usage: canary-env.sh <file> KEY [KEY ...] [NAME=value ...]" >&2
  exit 64
fi
file=$1
shift
mkdir -p "$(dirname "$file")"
: > "$file"
for arg in "$@"; do
  case "$arg" in
    *=*)
      if ! printf '%s' "${arg%%=*}" | grep -qE '^[A-Za-z_][A-Za-z0-9_]*$'; then
        echo "canary-env.sh: not a variable name: ${arg%%=*}" >&2
        exit 64
      fi
      printf '%s\n' "$arg" >> "$file"
      ;;
    *)
      if ! printf '%s' "$arg" | grep -qE '^[A-Za-z_][A-Za-z0-9_]*$'; then
        echo "canary-env.sh: not a variable name: $arg" >&2
        exit 64
      fi
      tag=$(printf '%s' "$arg" | tr 'A-Z_' 'a-z-')
      hex=$(od -An -N3 -tx1 /dev/urandom | tr -d ' \n')
      printf '%s=CANARY-%s-%s\n' "$arg" "$tag" "$hex" >> "$file"
      ;;
  esac
done
echo "wrote $file"
