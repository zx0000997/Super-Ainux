# M0 — Baseline host, single-node deploy, secrets & config

This tree implements milestone **M0** from [docs/SAS_SYSTEM_SPEC.zh.md](../docs/SAS_SYSTEM_SPEC.zh.md) (baseline Linux posture, one-node orchestration, split secrets/config). It does **not** include M1+ services (task API, audit, LLM adapters).

| Area | Path |
|------|------|
| OS baseline & SBOM | [baseline/BASELINE.md](baseline/BASELINE.md) |
| Host install & Compose | [deploy/install.sh](deploy/install.sh), [deploy/compose.yaml](deploy/compose.yaml) |
| Firewall (nftables) | [firewall/](firewall/) |
| Non-secret config + JSON Schema | [config/](config/) |
| Operator / Supervisor secret layout | [secrets/](secrets/) |
| Minimal `/health` service | [services/health-nginx/](services/health-nginx/) |

End-to-end acceptance (fresh VM → health + fake keys): [docs/M0_DEPLOYMENT.zh.md](../docs/M0_DEPLOYMENT.zh.md).
