#!/usr/bin/env bash
# Install M0 baseline packages and deploy the health stack under /opt/super-ainux/m0.
# Usage: sudo ./install.sh   (from repo: m0/deploy/install.sh)

set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
M0_ROOT="$(cd "${DEPLOY_DIR}/.." && pwd)"
INSTALL_ROOT="${INSTALL_ROOT:-/opt/super-ainux/m0}"

if [[ ! -f "${M0_ROOT}/baseline/packages-debian12.txt" ]]; then
  echo "Cannot find M0 tree at ${M0_ROOT}" >&2
  exit 1
fi

if [[ -f /etc/os-release ]]; then
  # shellcheck source=/dev/null
  . /etc/os-release
else
  echo "Missing /etc/os-release" >&2
  exit 1
fi

case "${ID:-}" in
  debian|ubuntu) ;;
  *)
    echo "Unsupported OS ID=${ID:-unknown}. Use Debian 12 or Ubuntu 22.04+ manually." >&2
    exit 1
    ;;
esac

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
mapfile -t PACKAGES < <(grep -v '^#' "${M0_ROOT}/baseline/packages-debian12.txt" | grep -v '^$' || true)
if [[ "${#PACKAGES[@]}" -eq 0 ]]; then
  echo "No packages listed in packages-debian12.txt" >&2
  exit 1
fi
apt-get install -y "${PACKAGES[@]}"

install -d "${INSTALL_ROOT}"
rsync -a --delete \
  --exclude '.git/' \
  "${M0_ROOT}/" "${INSTALL_ROOT}/"

COMPOSE_CMD=()
if podman compose version &>/dev/null; then
  COMPOSE_CMD=(podman compose)
elif command -v podman-compose &>/dev/null; then
  COMPOSE_CMD=(podman-compose)
else
  echo "Neither 'podman compose' nor podman-compose found after install." >&2
  exit 1
fi

cd "${INSTALL_ROOT}/deploy"
"${COMPOSE_CMD[@]}" -f compose.yaml build
"${COMPOSE_CMD[@]}" -f compose.yaml up -d

install -d /etc/systemd/system
sed "s|__INSTALL_ROOT__|${INSTALL_ROOT}|g" "${INSTALL_ROOT}/deploy/sas-m0-compose.service.in" \
  > /etc/systemd/system/sas-m0-compose.service
systemctl daemon-reload
systemctl enable sas-m0-compose.service

echo "M0 installed to ${INSTALL_ROOT}"
echo "Health: curl -sf http://127.0.0.1:18080/health"
echo "Optional: sudo ${INSTALL_ROOT}/firewall/apply-firewall.sh"
