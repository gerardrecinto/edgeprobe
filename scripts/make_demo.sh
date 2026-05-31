#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$ROOT/src" python3 -m edgeprobe analyze "$ROOT/tests/fixtures/host-snapshot"

