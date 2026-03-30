# M0 secrets layout

SAS requires **split storage** for Operator vs Supervisor credentials ([SAS_SYSTEM_SPEC.zh.md](../../docs/SAS_SYSTEM_SPEC.zh.md) §3, §10).

## File-based (default for M0)

| File | Content |
|------|---------|
| `operator.env` (from [operator.env.example](operator.env.example)) | `OPERATOR_API_KEY` only |
| `supervisor.env` (from [supervisor.env.example](supervisor.env.example)) | `SUPERVISOR_API_KEY` only |

Deploy on the host (example):

```bash
sudo install -d -m 0750 -o root -g root /etc/super-ainux
sudo install -m 0600 -T operator.env.example /etc/super-ainux/operator.env   # after editing
sudo install -m 0600 -T supervisor.env.example /etc/super-ainux/supervisor.env
```

Validate together with non-secret JSON:

```bash
python3 ../config/validate_config.py \
  --runtime /etc/super-ainux/sas-runtime.json \
  --operator-env /etc/super-ainux/operator.env \
  --supervisor-env /etc/super-ainux/supervisor.env
```

## SOPS + age (optional, Git-friendly ciphertext)

1. Install `age` and `sops` (see [packages-debian12.txt](../baseline/packages-debian12.txt) comments).
2. Generate a key: `age-keygen -o ~/.config/sops/age/keys.txt`
3. Create `.sops.yaml` at repo root listing age recipient(s) — **do not commit the private key**.
4. `sops operator.env` → edit → file on disk is encrypted; decrypt only on deploy host.

Example `.sops.yaml` fragment:

```yaml
creation_rules:
  - path_regex: m0/secrets/.*\.enc\.yaml$
    age: age1...
```

## Rotation & incident (manual runbook)

1. **Rotate**: issue new API keys at each vendor; update the env file or SOPS secret; restart affected services (M1+); revoke old keys at vendor console.
2. **Leak**: revoke immediately at vendor; assume `operator.env` / `supervisor.env` compromised if stored together with runtime backup — rotate both if unsure; re-validate with `validate_config.py`.

## CI

- Never commit `.env` with real keys. Use `*.env.example` only in Git.
- PR checks should grep for high-entropy key patterns if you add application code later.
