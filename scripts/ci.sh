#!/usr/bin/env bash
set -euo pipefail

# The whole validation suite is `make check`, and that is the only sequence.
# This wrapper exists so the entry point matches q_frontend and q_backend;
# it deliberately adds no step of its own, because a second list of checks is
# a second thing to keep in sync with CI.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=================================================="
echo "==> Running q_contracts CI Pipeline"
echo "=================================================="

make check

echo "=================================================="
echo "==> All q_contracts checks passed successfully!"
echo "=================================================="
