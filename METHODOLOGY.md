# 🎯 Bug Bounty Methodology

A step-by-step workflow I follow for every target — from recon to reporting.
Each phase links back to the relevant notes in this repo where applicable.

> **How to use this:** Copy the checklist for a new target into a scratch file (or a GitHub Issue in this repo) and tick off phases as you go. Don't skip phases — most missed bugs come from skipping recon, not from missing a "fancy" payload.

---

## 🗺️ Workflow Overview

```
Recon → Subdomain Enum → Live Filtering → URL/Endpoint Gathering
   → Target Triage → Content Discovery → Automated Scanning
   → Manual Testing → Reporting
```

---

## Phase 0 — Scope & Setup

- [ ] Read the program's scope page fully (in-scope domains, wildcards, excluded assets, reward table)
- [ ] Note any rate-limit / testing restrictions
- [ ] Create a target folder: `targets/<program-name>/`
- [ ] Save scope to `scope.txt` for use in later commands

---

## Phase 1 — Subdomain Enumeration

**Goal:** Build the widest possible attack surface before narrowing down.

- [ ] Passive enumeration (subfinder, assetfinder, amass passive, crt.sh, GitHub dorking)
- [ ] Active/brute-force enumeration (puredns / shuffledns + resolvers list + wordlist)
- [ ] Merge + dedupe all sources into one `all_subs.txt`
- [ ] Permutation/mutation scan on discovered subdomains (dnsgen / alterx) to catch dev/staging/api variants

📁 *Reference: `USEFUL-COMMANDS/` for exact command syntax*

---

## Phase 2 — Live Host Filtering

**Goal:** Cut noise, keep only what's actually reachable.

- [ ] Resolve DNS (dnsx) to remove dead entries
- [ ] Probe for live HTTP(S) services (httpx) → capture status code, title, tech stack, content-length
- [ ] Save output as `live_subs.txt`
- [ ] Screenshot live hosts (gowitness/aquatone) for a fast visual skim

---

## Phase 3 — URL & Endpoint Gathering

**Goal:** Map every reachable path/parameter across the live scope.

- [ ] Historical URLs (gau / waybackurls / katana with crawl)
- [ ] Merge with a JS-crawl pass to pull endpoints out of JavaScript files
- [ ] Extract & dedupe parameters (unfurl / gf patterns) into categories: `xss-candidates.txt`, `sqli-candidates.txt`, `redirect-candidates.txt`, `lfi-candidates.txt`, `idor-candidates.txt`
- [ ] Extract JS files separately → run `secretfinder`/`trufflehog`-style scan for leaked keys/endpoints

📁 *Reference: `DORKS/` for Google/GitHub dork lists to supplement this*

---

## Phase 4 — Target Triage ("Juicy" Subdomain Picking)

**Goal:** Don't test 3,000 hosts equally — prioritize.

Rank live subdomains by signal:
- [ ] Interesting keywords: `admin`, `internal`, `staging`, `dev`, `api`, `portal`, `test`, `vpn`
- [ ] Unusual tech stack / outdated server headers (httpx `-tech-detect`)
- [ ] Login/auth pages present (higher chance of auth flaws)
- [ ] File upload or account-management functionality visible
- [ ] Anything returning 403/401 (possible bypass target — see `BYPASSES/`)

Produce a short list: `priority_targets.txt`

---

## Phase 5 — Content & Directory Discovery

**Goal:** Find hidden paths on the priority list.

- [ ] Directory/file brute-force on priority targets (ffuf/feroxbuster + good wordlist)
- [ ] Try common backup/config extensions (`.bak`, `.zip`, `.env`, `.git/`)
- [ ] Check for exposed API docs (`/swagger`, `/graphql`, `/api-docs`)

📁 *Reference: `DIRECTORY-BRUTEFORCING/`*

---

## Phase 6 — Automated Vulnerability Scanning

**Goal:** Cheap wins first, before manual effort.

- [ ] Run nuclei across **all** live subdomains (not just priority list) with updated templates
- [ ] Separate nuclei runs: CVEs, misconfig, exposures, default-logins templates
- [ ] Subdomain takeover check (nuclei takeover templates / subjack / can-i-take-over-xyz list)
- [ ] Triage nuclei findings — false-positive check before reporting anything

---

## Phase 7 — Manual Testing (Priority Targets)

**Goal:** This is where the real bounties are. Work top-down through your priority list.

For each priority target, walk through the relevant checklist below:

| Area | Notes folder |
|---|---|
| Authentication flaws | `AUTHENTICATION-FLAWS/` |
| 2FA bypass | `2FA-BYPASS/` |
| Password reset flow | `PASSWORD-RESET/` |
| IDOR / broken access control | `IDOR/` |
| Business logic flaws | `BUSINESS-LOGIC/` |
| XSS (reflected/stored/DOM) | `XSS/` |
| SQL injection | `SQL-INJECTION/` |
| LFI / path traversal | `LFI/` |
| Open redirect | `OPEN-REDIRECT/` |
| File upload flaws | `FILE-UPLOAD/` |
| Host header injection | `HOST-HEADER-INJECTION/` |
| WAF/rate-limit/403 bypasses | `BYPASSES/` |

- [ ] Test each area systematically per target rather than jumping between targets mid-test
- [ ] Log every test attempted (even negative results) — saves re-testing later

---

## Phase 8 — Reporting

- [ ] Reproduce the bug cleanly, minimal steps
- [ ] Capture proof (screenshot/video/request-response)
- [ ] Write impact clearly — what can an attacker *actually* do with this
- [ ] Submit, then log the report in a `reports.md` tracker with status (submitted/triaged/paid/duped)

---

## 📌 Quick Reference: Tool Chain by Phase

| Phase | Primary Tools |
|---|---|
| Subdomain enum | subfinder, amass, assetfinder, puredns |
| Live filtering | dnsx, httpx |
| URL gathering | gau, waybackurls, katana |
| Screenshots | gowitness / aquatone |
| Dir bruteforce | ffuf, feroxbuster |
| Vuln scanning | nuclei |
| Takeover check | nuclei (takeover templates), subjack |

---

## ✅ Per-Target Checklist (copy this for every new target)

```markdown
### Target: 
- [ ] Scope reviewed
- [ ] Subdomain enum done
- [ ] Live hosts filtered
- [ ] URLs/endpoints gathered
- [ ] Priority targets picked
- [ ] Directory bruteforce done
- [ ] Nuclei scan done
- [ ] Subdomain takeover checked
- [ ] Manual testing — auth
- [ ] Manual testing — IDOR
- [ ] Manual testing — XSS
- [ ] Manual testing — SQLi
- [ ] Manual testing — business logic
- [ ] Manual testing — other categories
- [ ] Reports submitted
```
