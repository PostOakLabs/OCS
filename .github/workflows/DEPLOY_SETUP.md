# GitHub Actions deploy setup — The Omega Centauri Society

One-time checklist. Complete every item before the first push to `main`.

---

## Step 1 — Confirm DreamHost shell access

> **Critical.** SFTP-only accounts accept SSH handshakes but silently drop
> remote commands. rsync will hang until the job times out and you'll see no
> useful error. Shell access is required.

1. Log in to the DreamHost panel → **Manage Users**.
2. Click **Edit** next to the deploy user.
3. Under "User type", confirm it is set to **Shell user** (not SFTP/FTP).
4. Save if you changed it; the change takes ~5 minutes to propagate.

---

## Step 2 — Generate an ed25519 deploy key

Run on your local machine (not on the server):

```bash
ssh-keygen -t ed25519 -C "ocs-github-deploy" -f ~/.ssh/ocs_deploy_key -N ""
```

This creates two files:

| File | Purpose |
|---|---|
| `~/.ssh/ocs_deploy_key` | Private key → goes into GitHub secret `DH_SSH_KEY` |
| `~/.ssh/ocs_deploy_key.pub` | Public key → goes onto DreamHost server |

**Do not protect the key with a passphrase** (`-N ""`). GitHub Actions cannot
enter a passphrase interactively.

---

## Step 3 — Install the public key on DreamHost

```bash
ssh-copy-id -i ~/.ssh/ocs_deploy_key.pub YOUR_USER@YOUR_DREAMHOST_HOST
```

Or manually: append the contents of `ocs_deploy_key.pub` to
`~/.ssh/authorized_keys` on the DreamHost server.

Verify it works before adding it to GitHub:

```bash
ssh -i ~/.ssh/ocs_deploy_key -o IdentitiesOnly=yes YOUR_USER@YOUR_DREAMHOST_HOST "echo ok"
```

Expected output: `ok`

---

## Step 4 — Add the five repository secrets

In GitHub: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `DH_SSH_KEY` | Full contents of `~/.ssh/ocs_deploy_key` (the private key). Include the `-----BEGIN...` and `-----END...` lines. |
| `DH_SSH_USER` | Your DreamHost shell username (e.g. `ocsdeploy`) |
| `DH_SSH_HOST` | DreamHost server hostname (e.g. `sub1.dreamhost.com`) — find it in the panel under **Manage Users → Edit → SSH** or in the welcome email |
| `DH_WEB_ROOT` | Absolute path to the web root on DreamHost (e.g. `/home/ocsdeploy/omegacentauri.me`) |
| `DH_SITE_URL` | Canonical site URL for the smoke test (e.g. `https://omegacentauri.me`) |

---

## Step 5 — First deploy

**Recommended: run a dry run first.**

1. GitHub → **Actions** → **Deploy to DreamHost** → **Run workflow**
2. Set **dry_run** to `true`.
3. Watch the rsync output in the "rsync dry run" step — it shows every file
   that *would* be transferred without actually sending anything.
4. If the output looks right, re-run with **dry_run** set to `false`.

Subsequent deploys happen automatically on every push to `main`.

---

## Files excluded from deploy

The following are never synced to DreamHost:

- `.git/` `.github/`
- `CLAUDE.md`
- `.DS_Store`

Dev-only docs (`HANDOVER_*.md`, `HUB_AND_DEMOS_PLAN_*.md`,
`ocs-tools-spec-v1.1.md`, `AUDIT-*.md`) live outside the `repo/` directory
entirely and are never touched by rsync regardless.

Everything else inside `repo/` — HTML, images, `llms.txt`, `humans.txt`,
`robots.txt`, `sitemap.xml`, `LICENSE-*.md`, `CONTRIBUTING.md`, and all tool
files — is deployed.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| rsync hangs indefinitely | DreamHost user is SFTP-only, not Shell | Step 1 above |
| `Permission denied (publickey)` | Public key not in `authorized_keys` | Step 3 above |
| SSH test passes, rsync fails | Wrong `DH_WEB_ROOT` path | Check the absolute path in DH panel |
| Smoke test returns 4xx/5xx | Files didn't land in the right directory | Verify `DH_WEB_ROOT` matches the actual document root |
| Smoke test returns 301 | HTTP→HTTPS redirect — this is expected and passes ✅ | No action needed |
