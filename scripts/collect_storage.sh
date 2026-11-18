#!/usr/bin/env bash
# Add storage and bond files to a snapshot directory from this host.
# Usage: scripts/collect_storage.sh OUTDIR   (read-only; zpool is optional)
set -u
out="${1:?usage: collect_storage.sh OUTDIR}"
mkdir -p "$out"
[ -r /proc/mdstat ] && cp /proc/mdstat "$out/proc_mdstat.txt"
cp /proc/mounts "$out/proc_mounts.txt"
if ls /proc/net/bonding/* >/dev/null 2>&1; then
  cat /proc/net/bonding/* > "$out/proc_net_bonding.txt"
fi
if command -v zpool >/dev/null 2>&1 && [ -n "$(zpool list -H 2>/dev/null)" ]; then
  zpool status > "$out/zpool_status.txt"
fi
uname -r > "$out/kernel_release.txt"
cp /proc/cmdline "$out/proc_cmdline.txt"
echo "wrote $out"
