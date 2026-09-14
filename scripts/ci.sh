#!/usr/bin/env bash
set -euo pipefail

# GUI-spawned git hooks (GitKraken, etc.) often omit the user session bus vars,
# which makes `systemctl --user` fail and skips ci.slice entirely.
if [[ -z "${XDG_RUNTIME_DIR:-}" && -d "/run/user/$(id -u)" ]]; then
  export XDG_RUNTIME_DIR="/run/user/$(id -u)"
fi
if [[ -z "${DBUS_SESSION_BUS_ADDRESS:-}" && -n "${XDG_RUNTIME_DIR:-}" && -S "${XDG_RUNTIME_DIR}/bus" ]]; then
  export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
fi

# Enter the host user ci.slice when available so local CI yields to interactive work.
# Scope gets Nice=10 + idle ionice so install/clone/build IO is deprioritized too.
# No-ops on hosts/runners without systemd-run or the slice (e.g. GitHub Actions).
if [[ "${CI_RESOURCE_CONTROLLED:-0}" != "1" ]]; then
  if command -v systemd-run >/dev/null 2>&1 &&
     systemctl --user status ci.slice >/dev/null 2>&1; then
    _ci_run=(
      systemd-run --user --scope --quiet --collect --slice=ci.slice --nice=10
      --setenv=CI_RESOURCE_CONTROLLED=1
      --setenv=XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR}"
      --setenv=DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS}"
    )
    if command -v ionice >/dev/null 2>&1; then
      exec "${_ci_run[@]}" ionice -c 3 "$0" "$@"
    fi
    exec "${_ci_run[@]}" "$0" "$@"
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
