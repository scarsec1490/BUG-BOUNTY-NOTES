# 🔐 Directory Bruteforcing Methodology

> **A practical and efficient approach to directory bruteforcing — focused on quality over quantity.**

> **Author: ShahidKhan**

---

<div align="center">

![Methodology](https://img.shields.io/badge/Type-Offensive%20Security-red?style=for-the-badge)
![Phase](https://img.shields.io/badge/Phase-Recon%20%26%20Enumeration-blue?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Smart%20%26%20Targeted-green?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Subdomain Enumeration & Filtering](#-1-subdomain-enumeration--filtering)
2. [Analyze robots.txt](#-2-analyze-robotstxt)
3. [Extract Paths from JavaScript Files](#-3-extract-paths-from-javascript-files)
4. [Identify Technologies](#-4-identify-technologies)
5. [Smart Directory Bruteforcing](#-5-smart-directory-bruteforcing)
6. [Handle 403 Forbidden Paths](#-6-handle-403-forbidden-paths)
7. [Summary Workflow](#️-summary-workflow)

---

## 🔍 1. Subdomain Enumeration & Filtering

Avoid blindly attacking the main domain. Start by collecting as many subdomains as possible from **multiple sources**, then intelligently filter for high-value targets.

### Why Filter First?
- Reduces noise and wasted requests
- Focuses effort on endpoints likely to expose sensitive functionality
- Speeds up overall recon significantly

### 🎯 High-Value Subdomain Filter

Use this one-liner to grep for subdomains worth targeting:

```bash
grep -Ei "admin|administrator|panel|dashboard|manage|control|api|rest|graphql|v[0-9]+|dev|test|testing|stage|staging|qa|uat|preprod|sandbox|login|signin|signup|auth|sso|oauth|account|user|profile|session|token|jwt|verify|reset|password|otp|mfa|2fa|cdn|static|media|assets|files|storage|upload|download|bucket|s3|blob|old|backup|bak|legacy|archive|copy|clone|monitor|monitoring|status|health|metrics|alert|grafana|prometheus|kibana|elastic|logs|debug|trace|tmp|cache|error|dump|aws|gcp|azure|cloud|k8s|docker|jenkins|ci|cd|git|gitlab|github|bitbucket|service|gateway|proxy|edge|backend|billing|payment|invoice|order|cart|wallet|transaction|internal|private"
```

### Categories to Focus On

| Category | Keywords |
|---|---|
| 🔑 Auth & Accounts | `login`, `auth`, `sso`, `oauth`, `jwt`, `mfa`, `2fa` |
| ⚙️ Admin & Control | `admin`, `panel`, `dashboard`, `manage`, `control` |
| 🚧 Dev & Test | `dev`, `test`, `staging`, `qa`, `uat`, `preprod`, `sandbox` |
| 📁 Storage & Files | `cdn`, `upload`, `storage`, `s3`, `blob`, `bucket` |
| 🧰 DevOps & CI/CD | `jenkins`, `gitlab`, `github`, `ci`, `cd`, `k8s`, `docker` |
| 💰 Billing & Payments | `billing`, `payment`, `invoice`, `wallet`, `transaction` |
| 📊 Monitoring | `grafana`, `prometheus`, `kibana`, `elastic`, `metrics` |
| 🗃️ Legacy & Backups | `old`, `backup`, `bak`, `legacy`, `archive`, `clone` |

---

## 🤖 2. Analyze `robots.txt`

The `robots.txt` file often **intentionally hides** paths it doesn't want indexed — which are exactly the paths you want to check.

### What to Look For
- Disallowed paths that suggest admin panels
- Internal API routes
- Hidden directories or staging endpoints

### Automation

Use **RoboHunter** to automate `robots.txt` collection across all subdomains:

🔗 [https://github.com/scarsec1490/RoboHunter](https://github.com/scarsec1490/RoboHunter)


## 📜 3. Extract Paths from JavaScript Files

JavaScript files are a **goldmine** for undocumented or hidden endpoints. Most modern web apps embed their entire API surface inside JS bundles.

### What to Look For
- 🔌 API route definitions (`/api/v1/`, `/internal/`, etc.)
- 🛤️ Hidden frontend routes
- 🔐 Authentication endpoints
- 🗝️ Hardcoded credentials or tokens *(bonus finding!)*

### Tool: Dirextractor

Use my tool **Dirextractor** to automatically parse JS files and build a custom, target-specific wordlist:

```
python3 dirextractor.py -i jsfiles.txt -o js-wordlist.txt
```

> 💡 **Why this matters:** A wordlist built from the target's own JS is infinitely more relevant than any generic wordlist.

### Manual Regex to Find Endpoints in JS

```bash
# Find API routes in JS files
grep -Eo '("|'"'"')(\/[a-zA-Z0-9_\-\/]+)("|'"'"')' target.js | sort -u

# Find fetch/axios calls
grep -Eo 'fetch\(["'"'"'][^"'"'"']+["'"'"']\)' target.js
```

---

## 🧠 4. Identify Technologies

Before bruteforcing, **fingerprint your target**. Using the wrong wordlist is a waste of time and requests.

### Key Things to Identify

| Target Info | Why It Matters |
|---|---|
| **Language** (PHP, Java, .NET, Python) | File extensions to look for (`.php`, `.jsp`, `.aspx`) |
| **Server** (Apache, Nginx, IIS) | Server-specific paths and configs |
| **Framework / CMS** (WordPress, Laravel, Django) | Known default paths and admin panels |
| **Cloud Provider** (AWS, GCP, Azure) | Storage buckets, metadata endpoints |

### Detection Methods

```bash
# Check response headers
curl -I https://target.com

# Use WhatWeb for tech fingerprinting
whatweb https://target.com

# Use Wappalyzer browser extension for quick visual fingerprinting
```

### Wordlist Selection Based on Tech

```
PHP Target     → Use PHP-specific wordlists (includes .php extensions)
WordPress      → Use WordPress-specific paths (/wp-admin, /wp-content, etc.)
Java / Spring  → Look for /actuator, /jolokia, /swagger-ui
.NET           → Look for .aspx, .asmx, /elmah.axd
```

---

## 📂 5. Smart Directory Bruteforcing

Start **small and targeted**, then expand based on results. Never start with massive wordlists.

### Phase 1 — Start Small

```bash
# Start with common, high-hit-rate wordlists
ffuf -u https://target.com/FUZZ -w /path/to/common.txt -mc 200,301,302,403

# Or with feroxbuster
feroxbuster -u https://target.com -w common.txt
```

### Phase 2 — Expand on Findings

Once you find valid paths, go deeper with larger lists:

```bash
# Use raft-small or raft-medium for broader coverage
ffuf -u https://target.com/found-dir/FUZZ -w raft-medium.txt

# Add technology-specific extensions
ffuf -u https://target.com/FUZZ -w wordlist.txt -e .php,.bak,.old,.conf,.sql
```

### Recommended Wordlists (Priority Order)

```
1. custom-from-js.txt        ← Built from target's own JS files (highest value)
2. common.txt                ← Quick wins, fast scan
3. raft-small.txt            ← Broader coverage
4. raft-medium.txt           ← Deep dive after initial findings
5. technology-specific.txt   ← Framework/CMS-specific paths
```

### Useful Flags & Tips

```bash
# Filter by response size to remove false positives
ffuf -u https://target.com/FUZZ -w wordlist.txt -fs 1234

# Set concurrency to avoid rate-limiting
ffuf -u https://target.com/FUZZ -w wordlist.txt -t 50

# Follow redirects
ffuf -u https://target.com/FUZZ -w wordlist.txt -r
```

---

## 🚫 6. Handle 403 Forbidden Paths

A `403 Forbidden` response means the path **exists** but access is restricted. These are **high-value targets**.

### Save 403s Separately 

### 403 Bypass Techniques

#### 🔀 Path Manipulation
```
/admin          → /%2fadmin
/admin          → /admin/
/admin          → /admin/.
/admin          → //admin//
/admin          → /./admin/./
```

#### 📝 Header Manipulation
```http
X-Original-URL: /admin
X-Rewrite-URL: /admin
X-Custom-IP-Authorization: 127.0.0.1
X-Forwarded-For: 127.0.0.1
X-Remote-IP: 127.0.0.1
X-Client-IP: 127.0.0.1
Referer: https://target.com/admin
```

#### 🔡 Case & Encoding Tricks
```
/admin   → /Admin
/admin   → /ADMIN
/admin   → /%61dmin
```

> 🎯 403 paths that bypass restrictions are often **critical vulnerabilities** — document them carefully.

---

## 🧠 Final Tip

<div align="center">

| ❌ Don't | ✅ Do |
|---|---|
| Rely on random generic wordlists | Build custom wordlists from JS analysis |
| Blindly attack the main domain | Target high-value subdomains first |
| Ignore 403 responses | Save and revisit with bypass techniques |
| Use massive wordlists from the start | Start small, expand on real findings |
| Skip tech fingerprinting | Identify stack before choosing wordlists |

</div>

---

## ⚔️ Summary Workflow

```
┌─────────────────────────────────────────────────┐
│           DIRECTORY BRUTEFORCING WORKFLOW        │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. 🔍 Enumerate Subdomains                     │
│         ↓                                       │
│  2. 🎯 Filter High-Value Targets (grep)         │
│         ↓                                       │
│  3. 🤖 Analyze robots.txt (RoboHunter)          │
│         ↓                                       │
│  4. 📜 Extract Endpoints from JS (Dirextractor) │
│         ↓                                       │
│  5. 🧠 Identify Technologies (WhatWeb, Headers) │
│         ↓                                       │
│  6. 📂 Smart Bruteforce (small → large lists)   │
│         ↓                                       │
│  7. 🚫 Save & Revisit 403 Endpoints             │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

<div align="center">

### 🔥 The key is not more requests — it's **smarter** requests.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
