#!/usr/bin/env bash
# Apply nftables ruleset for M0 (SSH only on WAN-facing input).
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES="${SCRIPT_DIR}/nftables-sas-m0.nft"

if ! command -v nft &>/dev/null; then
  echo "nftables (nft) not installed." >&2
  exit 1
fi

nft -f "${RULES}"
systemctl enable nftables 2>/dev/null || true
echo "Applied ${RULES}. Verify SSH access before closing session."
