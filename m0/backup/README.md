# Backup placeholder (M0)

SAS spec §11 requires backup policy for user data and audit. M0 only reserves layout:

- Suggested state directory (future): `/var/lib/super-ainux/`
- Suggested backup target: operator-maintained rsync/restic to external disk or NAS

## Systemd stubs (optional)

You can enable a no-op timer as a reminder hook:

```bash
sudo cp sas-m0-backup-placeholder.service sas-m0-backup-placeholder.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sas-m0-backup-placeholder.timer
```

Replace the `ExecStart` unit with your real backup script in a later milestone.
