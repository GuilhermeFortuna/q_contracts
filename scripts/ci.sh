#!/usr/bin/env bash
set -euo pipefail

# Enter the host user ci.slice when available so local CI yields to interactive work.
# No-ops on hosts/runners without systemd-run or the slice (e.g. GitHub Actions).
if [[ "${CI_RESOURCE_CONTROLLED:-0}" != "1" ]]; then
  if command -v systemd-run >/dev/null 2>&1 &&
     systemctl --user status ci.slice >/dev/null 2>&1; then
    exec systemd-run \
      --user --scope --quiet --collect \
      --slice=ci.slice \
      --setenv=CI_RESOURCE_CONTROLLED=1 \
      "$0" "$@"
  fi
fi

# The whole validation suite is `make check-suite`. `make check` and this script
# both enter here so hooks, GHA, and agents share one entrypoint.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=================================================="
echo "==> Running q_contracts CI Pipeline"
echo "=================================================="

make check-suite

echo "=================================================="
echo "==> All q_contracts checks passed successfully!"
echo "=================================================="
