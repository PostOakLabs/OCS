# The Omega Centauri Society

[![Deploy to DreamHost](https://github.com/PostOakLabs/OCS/actions/workflows/deploy.yml/badge.svg)](https://github.com/PostOakLabs/OCS/actions/workflows/deploy.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20689279.svg)](https://doi.org/10.5281/zenodo.20689279)
[![License: MIT (code)](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE-code.md)

Cite this software using [`CITATION.cff`](CITATION.cff) or the per-tool BibTeX entries at [omegacentauri.me/cite.html](https://omegacentauri.me/cite.html).

Browser-based science portal on NGC 5139 (Omega Centauri) — interactive calculators, observational proposals, and MCP-exposed tools for the IMBH evidence debate. Source for **[omegacentauri.me](https://omegacentauri.me)** — a scientific society dedicated to the study of Omega Centauri, the largest and most massive globular cluster in the Milky Way.

Citable: see [`CITATION.cff`](CITATION.cff) or the per-tool BibTeX entries at [omegacentauri.me/cite.html](https://omegacentauri.me/cite.html) (DOI: [10.5281/zenodo.20689279](https://doi.org/10.5281/zenodo.20689279)).

`🔭 Observational Proposals` &nbsp;`🛠️ Interactive Tools` &nbsp;`🌌 Globular Cluster Science` &nbsp;`📡 Multi-Messenger Astronomy` &nbsp;`💻 Static HTML`

---

## What's on the site

- **Observational proposals** — peer-reviewed instrument proposals spanning JWST, HST, MeerKAT, LIGO/Auger, IceCube, KM3NeT, Fermi/CTA, ELT/MICADO, and radio SETI
- **Interactive science tools** — browser-based calculators and simulators covering stellar dynamics, black hole physics, gravitational waves, cosmology, and SETI, plus multi-stage workflow chains. Current counts drift as tools ship — see `llms.txt` or run `python3 scripts/verify-counts.py`, never trust a hardcoded number here
- **Membership & advisors** — society structure, advisory board, and how to get involved
- **FAQ** — foundational questions about Omega Centauri and the society's mission

---

## Verifiable results

Every tool emits a hash-canonical artifact carrying a verifiable `execution_hash`, indexed in [`chaingraph.json`](chaingraph.json) — 28 tools, declaring OpenChainGraph spec `0.8.0` at conformance level **L4**. Recompute the hash from the same inputs and you get the same value; if a number moved, you find out rather than guess.

That matters more here than in most science tooling. A calculator that quietly changes its constants between the day you ran it and the day a referee checks it is worse than no calculator. The artifact pins the inputs, the canon version, and the output together.

Verify a result with the `verify_execution_hash` tool on the MCP server at [`mcp.omegacentauri.me/mcp`](https://mcp.omegacentauri.me/mcp), or in your own CI with [`ocg-verify-action`](https://github.com/PostOakLabs/ocg-verify-action) — zero dependencies, no call back to us.

The format is [OpenChainGraph](https://github.com/PostOakLabs/chaingraph), an open standard shared with [AINumbers.co](https://github.com/PostOakLabs/ainumbers) and [ApexLogics.org](https://github.com/PostOakLabs/apexlogics).

---

## Repository layout

```
OCS/
├── index.html                      ← Homepage
├── faq.html                        ← Frequently asked questions
├── advisors.html                   ← Advisory board
├── proposals.html                  ← Proposals index
├── proposal_*.html                 ← Individual instrument proposals
├── tools/                          ← Interactive science tools + workflow chains (see llms.txt for counts)
├── sitemap.xml                     ← XML sitemap
├── robots.txt                      ← Crawler directives
├── llms.txt                        ← LLM-readable site summary
├── humans.txt                      ← humans.txt
├── og-image.png                    ← Open Graph image
├── favicon.ico / favicon.svg       ← Favicons
├── LICENSE-code.md                 ← Code license
├── LICENSE-content.md              ← Content license
├── LICENSE-data.md                 ← Data license
├── CONTRIBUTING.md                 ← Contribution guidelines
└── .github/workflows/deploy.yml   ← CI/CD deploy pipeline
```

---

## Deploy pipeline

Every push to `main` validates and deploys automatically to DreamHost shared hosting via rsync over SSH.

| Trigger | Result |
|---|---|
| Push to `main` | Validate → deploy |
| Manual run (Actions → *Run workflow*) | Validate → deploy |
| Manual run with `dry_run: true` | Validate → rsync rehearsal only, no transfer |

Steps: secrets check → SSH key install → connectivity test → rsync dry run → rsync live deploy → smoke test.

The deploy is additive only — files on the server but absent from this repo are left untouched.

---

## Running the tests

The validate job runs two `node --test` suites:

```bash
node --test scripts/tests/tier-c-*.test.mjs
node --test scripts/tests/lib-imbh-constraints.test.mjs
```

No build step and no server needed. Node 18+ is enough.

---

## Editing the site

```bash
# Edit files, then:
git add -A
git commit -m "describe the change"
git push origin main
```

Preview locally: open `.html` files in a browser, or run `python3 -m http.server` from the repo root.

---

## One-time deployment setup

<details>
<summary>Expand for SSH key + DreamHost secret configuration</summary>

### 1. Enable shell access on the DreamHost user

In the DreamHost panel: **Websites → Manage Users → edit the user → set account type to "Shell".**
rsync requires SSH/shell access — SFTP-only will not work.

### 2. Generate a deploy key pair

```powershell
ssh-keygen -t ed25519 -f "C:\Users\<you>\.ssh\ocs_deploy_key" -C "ocs-github-deploy" -N '""'
```

### 3. Add the public key to DreamHost

```powershell
type C:\Users\<you>\.ssh\ocs_deploy_key.pub | ssh <dh-user>@<dh-host> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

Take `<dh-user>` and `<dh-host>` from the DreamHost panel — they're the same values you'll store as `DH_SSH_USER` and `DH_SSH_HOST` below.

### 4. Add five repository secrets

**Settings → Secrets and variables → Actions → New repository secret:**

| Secret | Value |
|---|---|
| `DH_SSH_KEY` | Full contents of the private key file `ocs_deploy_key` |
| `DH_SSH_USER` | Shell username from the DreamHost panel |
| `DH_SSH_HOST` | Server hostname from the DreamHost panel |
| `DH_WEB_ROOT` | `/home/<dh-user>/omegacentauri.me` |
| `DH_SITE_URL` | `https://omegacentauri.me` |

Once secrets exist, the next push to `main` deploys automatically.

</details>

---

## Links

- [omegacentauri.me](https://omegacentauri.me) — live site
- [The Omega Centauri Society](https://omegacentauri.me) — science, tools, and proposals
