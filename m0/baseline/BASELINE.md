# M0 baseline — Debian 12 (bookworm) + Podman (M0a)

## Decision

For **fast path to SAS application work** (M0a), the project standardizes on:

- **Architecture**: `x86_64` (per SAS spec).
- **OS**: **Debian 12 (bookworm)** minimal server install, or derivative with compatible `apt` (e.g. Ubuntu 22.04 LTS where noted).
- **Container runtime**: **Podman** + **podman-compose** (rootless supported; install script can use rootful for simplicity on a home server).
- **Custom kernel**: Optional. Production can run distro kernel; custom **Linux 6.19.8** build is documented in [kernel-notes.md](kernel-notes.md) and [OS_DEVELOPMENT_GUIDE.md](../../OS_DEVELOPMENT_GUIDE.md).

A future **M0b** can add Buildroot/Yocto images; this repo ships reproducible **package lists + scripts**, not a prebuilt `.img` binary.

## Version pinning

1. After install, capture versions:

   ```bash
   dpkg-query -W -f='${Package} ${Version}\n' > /opt/super-ainux/m0/baseline/installed-packages.snapshot.txt
   ```

2. Commit that snapshot next to [packages-debian12.txt](packages-debian12.txt) when you cut a release tag (e.g. `m0-2026.03.30`).

3. **Rollback**: reinstall from the same ISO/netinst + [packages-debian12.txt](packages-debian12.txt), then re-run [deploy/install.sh](../deploy/install.sh).

## Hardware assumptions

- UEFI or legacy BIOS PC / mini-PC.
- Single network interface with IPv4 (IPv6 optional).
- Disk ≥ 20 GiB for OS + container images + future SAS data.

## cloud-init (optional)

For VMs, see [cloud-init.yaml](cloud-init.yaml) as a starting point.
