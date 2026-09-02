# 🧩 API Security Testing Methodology

> **A complete, structured approach to testing REST/GraphQL APIs for security flaws — from recon to business logic abuse.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-API%20Security-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-Auth%20%7C%20AuthZ%20%7C%20Logic%20%7C%20Data-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Burp%20%2B%20Postman-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Phase 1 — Recon & Endpoint Mapping](#-phase-1--recon--endpoint-mapping)
2. [Phase 2 — Authentication Testing](#-phase-2--authentication-testing)
3. [Phase 3 — Authorization / BOLA & BFLA](#-phase-3--authorization--bola--bfla)
4. [Phase 4 — Mass Assignment & Excessive Data Exposure](#-phase-4--mass-assignment--excessive-data-exposure)
5. [Phase 5 — Input Validation & Injection](#-phase-5--input-validation--injection)
6. [Phase 6 — Rate Limiting & Resource Consumption](#-phase-6--rate-limiting--resource-consumption)
7. [Phase 7 — Business Logic Flaws](#-phase-7--business-logic-flaws)
8. [Phase 8 — HTTP Method & Content-Type Tampering](#-phase-8--http-method--content-type-tampering)
9. [Phase 9 — Versioning & Shadow/Zombie Endpoints](#-phase-9--versioning--shadowzombie-endpoints)
10. [Phase 10 — CORS & Header Misconfiguration](#-phase-10--cors--header-misconfiguration)
11. [Phase 11 — GraphQL-Specific Testing](#-phase-11--graphql-specific-testing)
12. [Phase 12 — SSRF & Server-Side Request Flaws](#-phase-12--ssrf--server-side-request-flaws)
13. [Phase 13 — Misc Lifecycle & Config Flaws](#-phase-13--misc-lifecycle--config-flaws)
14. [Summary Workflow](#️-summary-workflow)
15. [Quick Decision Tree](#-quick-decision-tree)

---

## 🔍 Phase 1 — Recon & Endpoint Mapping

Before sending payloads, build a complete map of the API surface.

### 1.1 — Subdomain Enumeration (from a domain list)

Start broad, then narrow down to anything that smells like an API.

```bash
# Enumerate subdomains for a single target
subfinder -d target.com -all -silent > subs.txt

# Enumerate for a LIST of domains (bug bounty program scope file)
subfinder -dL domains.txt -all -silent -o subs_raw.txt

# Merge with other sources for coverage
assetfinder --subs-only -f domains.txt >> subs_raw.txt
amass enum -passive -df domains.txt -o subs_amass.txt

# Dedup
cat subs_raw.txt subs_amass.txt | sort -u > all_subs.txt
```

### 1.2 — Filter for API-Related Subdomains (fully loaded grep)

Run this against `all_subs.txt` to pull out anything likely to be an API surface:

```bash
grep -Ei '^(api|apis|api[0-9]*|rest|restapi|graphql|gql|gateway|gw|ws|wss|socket|rpc|grpc|soap|internal|int|dev-api|stage-api|staging-api|test-api|uat-api|sandbox|sb|admin-api|partner-api|public-api|private-api|mobile-api|m-api|app-api|apidocs|api-docs|docs-api|swagger|openapi|apigee|apim|apigateway|edge|backend|be|bff|micro|microservice|services?|svc|v[0-9]+-api|api-v[0-9]+)\.' all_subs.txt | sort -u > api_subs.txt
```

> This catches common naming conventions: `api.`, `api1.`, `graphql.`, `gateway.`, `internal.`, `staging-api.`, `bff.`, `svc.`, `apidocs.`, versioned hosts like `v2-api.` etc. Tune the alternation list to what you see in the target's naming style.

### 1.3 — Probe for Alive Hosts + Fingerprint

```bash
cat api_subs.txt | httpx -silent -sc -title -td -ip -cl -o api_subs_alive.txt

# Grab JSON responses / non-HTML content-types specifically (likely raw APIs)
cat api_subs_alive.txt | httpx -silent -mc 200 -content-type | grep -Ei 'json|xml' 
```

### 1.4 — API Documentation & Schema Discovery

Check every live API host for exposed docs/specs — these hand you the entire endpoint list:

```bash
for host in $(cat api_subs_alive.txt | awk '{print $1}'); do
  for path in swagger.json swagger.yaml openapi.json openapi.yaml api-docs \
              v1/swagger.json v2/swagger.json swagger-ui.html swagger/index.html \
              api/swagger.json api/v1/swagger.json graphql graphiql \
              .well-known/openapi.json api/docs docs/api ; do
    url="${host}/${path}"
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    [[ "$code" == "200" ]] && echo "[+] $url"
  done
done
```

### 1.5 — Directory & Endpoint Fuzzing

Use a dedicated API wordlist (SecLists has good ones) against each live API host:

```bash
# Basic API path fuzzing with ffuf
ffuf -u https://api.target.com/FUZZ \
     -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt \
     -mc 200,201,204,301,302,307,401,403 \
     -t 50 -o ffuf_api.json -of json

# Version + path combo fuzzing
ffuf -u https://api.target.com/FUZZ1/FUZZ2 \
     -w versions.txt:FUZZ1 -w /usr/share/seclists/Discovery/Web-Content/api/objects.txt:FUZZ2 \
     -mc 200,401,403 -t 50

# Recursive fuzz with gobuster as a second pass
gobuster dir -u https://api.target.com -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt \
     -t 50 -x json,xml -b 404 -r
```

Where `versions.txt` is a small list you build: `v1`, `v2`, `v3`, `beta`, `internal`, `admin`, `stage`.

### 1.6 — Historical / Passive URL Collection (katana + gau + waybackurls)

```bash
# Active crawl
katana -u https://target.com -jc -kf all -d 5 -silent -o katana.txt

# Passive from multiple archives
gau target.com --subs --threads 10 > gau.txt
waybackurls target.com > wayback.txt
echo "target.com" | gauplus -subs -t 10 >> gau.txt   # optional extra source

# Merge + dedupe everything into one master file
cat katana.txt gau.txt wayback.txt | sort -u > allurls.txt
```

### 1.7 — Extract API Endpoints from allurls.txt (fully loaded grep)

```bash
grep -EiP '(\/(api|rest|graphql|gql|v[0-9]{1,2}|internal|admin|partner|mobile|service|services|svc|rpc|gateway)\/[^\s"'"'"'<>]*)|(\.(json|xml)(\?|$))|(\/(oauth|token|auth|login|register|reset[-_]?password|otp|2fa|verify|webhook|callback)\b[^\s"'"'"'<>]*)' allurls.txt | sort -u > api_endpoints.txt

# Then split further for quick triage:

# Only real API-prefixed paths
grep -Ei '/(api|rest|graphql|gql)/' allurls.txt | sort -u > endpoints_api_prefixed.txt

# Only versioned paths (v1, v2, v3...)
grep -EiP '/v[0-9]{1,2}/' allurls.txt | sort -u > endpoints_versioned.txt

# Auth / account-sensitive endpoints worth prioritizing
grep -Ei '/(auth|login|register|token|oauth|reset[-_]?password|otp|2fa|verify|session|account|admin|user|users|profile)\b' allurls.txt | sort -u > endpoints_sensitive.txt

# Endpoints with parameters (good injection/BOLA candidates)
grep -E '\?[a-zA-Z0-9_]+=' allurls.txt | sort -u > endpoints_with_params.txt

# JS files (mine these separately for hardcoded endpoints/keys)
grep -Ei '\.js(\?|$)' allurls.txt | sort -u > js_files.txt
```

### 1.8 — Mine JS Files for Hidden Endpoints

```bash
cat js_files.txt | httpx -silent -mc 200 | xargs -I{} curl -s {} | \
  grep -EoP '(?<=["'"'"'])\/[a-zA-Z0-9_\-\/\.]*(api|v[0-9])[a-zA-Z0-9_\-\/\.]*(?=["'"'"'])' | \
  sort -u > js_endpoints.txt

# Or use a purpose-built tool for higher accuracy
python3 LinkFinder.py -i js_files.txt -o cli >> js_endpoints.txt
```

### 1.9 — Wrap-Up

```
1. Cross-reference endpoints_sensitive.txt against BOLA/BFLA testing (Phase 3)
2. Feed endpoints_with_params.txt into injection fuzzing (Phase 5)
3. Note every parameter, header, and auth token used across the flow
4. Passively crawl the app in Burp while using every feature at least once,
   so anything missed by automation still gets manually mapped
```

> 💡 **Goal:** a full inventory of endpoints, methods, params, and auth requirements before touching a single payload.

---

## 🔑 Phase 2 — Authentication Testing

```
1. Identify auth mechanism: JWT, session cookie, API key, OAuth token
2. JWT checks:
     - alg: none acceptance
     - Signature not verified (swap payload, keep signature)
     - Weak/guessable HMAC secret (crack with hashcat/jwt_tool)
     - Key confusion (RS256 → HS256 using the public key as secret)
     - Missing expiry (exp) or long-lived tokens
3. API key checks:
     - Key sent in query string (logged, cached, leaked via Referer)
     - Same key works across environments (staging key on prod)
4. Test password reset / login endpoints for the same flaws covered
   in 2FA-Bypass.md (OTP reuse, response manipulation, no rate limit)
5. Check if authenticated endpoints work with an EXPIRED or LOGGED-OUT token
```

---

## 🧱 Phase 3 — Authorization / BOLA & BFLA

**BOLA (Broken Object Level Authorization) — the #1 API vuln.**

```
1. Get two accounts: Account A (yours) and Account B (victim/other role)
2. Perform an action as A, capture the request (e.g. GET /api/orders/1001)
3. Replay the SAME request using A's token but B's object ID:
     GET /api/orders/1002   (with A's Authorization header)
4. Check read AND write endpoints — GET, PUT, PATCH, DELETE
5. Try both incrementing IDs and UUIDs (UUIDs are guessed less often but
   still worth testing if leaked elsewhere, e.g. in another response)
```

**BFLA (Broken Function Level Authorization):**

```
1. Log in as a LOW-privilege user (e.g. regular user, not admin)
2. Identify admin-only endpoints from docs/JS (e.g. /api/admin/users)
3. Replay them using the low-privilege token
4. Also test HTTP method swaps on the same endpoint:
     GET /api/users/5      → allowed for user
     DELETE /api/users/5   → should be admin-only, test if it isn't
```

---

## 📦 Phase 4 — Mass Assignment & Excessive Data Exposure

### Mass Assignment

```
1. Capture a legitimate "update profile" or "create object" request
2. Add extra fields the UI doesn't expose but the backend might accept:
     {"name": "test", "isAdmin": true, "role": "admin", "balance": 99999}
3. Check the response / re-fetch the object to see if the extra field stuck
```

### Excessive Data Exposure

```
1. Compare what the UI displays vs. the RAW API response
2. Look for extra fields leaked in the JSON: password_hash, ssn, internal_notes,
   other_users_email, is_test_account, api_secret
3. This is common on "list" endpoints that return full objects instead of
   a filtered subset meant for the frontend
```

---

## 💉 Phase 5 — Input Validation & Injection

```
1. SQLi: inject on every parameter, including JSON body values, not just
   query strings — ' OR '1'='1, UNION SELECT, time-based (SLEEP(5))
2. NoSQLi: {"username": {"$ne": null}, "password": {"$ne": null}}
3. Command injection: ; whoami, | id, `id`, $(id) on any param that
   might touch a shell (file conversion, ping, export features)
4. XXE: if the API accepts XML, test external entity injection
5. SSTI: {{7*7}}, ${7*7}, <%= 7*7 %> on any field later rendered (emails,
   PDF generation, notifications)
6. Path traversal on any param used for file access: ../../etc/passwd
7. Fuzz every parameter with a large wordlist (Intruder / ffuf) for
   unexpected 500 errors that leak stack traces
```

---

## 🔓 Phase 6 — Rate Limiting & Resource Consumption

```
1. Send the same request 50-100x rapidly — check for 429 / lockout
2. Test rate limiting per-endpoint, not just globally (login may be limited,
   but /api/otp/resend or /api/export might not be)
3. Check if rate limit is IP-based only — bypass via header spoofing:
     X-Forwarded-For, X-Real-IP, X-Client-IP (rotate values)
4. Test for unbounded resource consumption:
     - Pagination: ?limit=999999999
     - Batch endpoints: submit thousands of items in one array
     - Regex fields prone to ReDoS
     - File upload size / zip-bomb handling
```

---

## 🧠 Phase 7 — Business Logic Flaws

```
1. Price/quantity manipulation: negative quantities, negative prices,
   float rounding abuse (0.001 × 1000 items)
2. Workflow/state-skipping: call step 3 of a multi-step API without
   completing steps 1-2 (e.g. skip payment, go straight to "order confirmed")
3. Race conditions: fire the SAME request (e.g. "redeem coupon",
   "withdraw funds") concurrently via Burp's "Send group in parallel"
   to see if a single-use resource can be used multiple times
4. Coupon/referral abuse: reuse single-use codes, self-referral loops
5. IDOR via non-ID identifiers: order numbers, invoice numbers, tracking
   codes — anything sequential or predictable
```

---

## 🔀 Phase 8 — HTTP Method & Content-Type Tampering

```
1. Swap methods on every endpoint: GET ↔ POST ↔ PUT ↔ PATCH ↔ DELETE
   (some frameworks route unhandled methods to less-guarded logic)
2. Try method override headers: X-HTTP-Method-Override: DELETE
3. Change Content-Type: application/json → application/xml,
   multipart/form-data, or text/plain — some parsers behave
   differently or skip validation for non-default types
4. Send malformed/duplicate keys in JSON body to test parser confusion:
     {"role":"user","role":"admin"}
```

---

## 🗂️ Phase 9 — Versioning & Shadow/Zombie Endpoints

```
1. If /api/v2/users blocks an attack, try /api/v1/users — old versions
   often lack the same validation/patches
2. Check for beta/internal/debug endpoints: /api/internal/, /api/debug/,
   /api/test/, /api/_admin
3. Try removing or adding trailing slashes, .json extensions, or case
   changes (/API/Users vs /api/users) — routing layers may treat them
   differently from auth middleware
```

---

## 🌐 Phase 10 — CORS & Header Misconfiguration

```
1. Send Origin: https://evil.com and check the response:
     Access-Control-Allow-Origin: https://evil.com
     Access-Control-Allow-Credentials: true
   → if both are present, this is exploitable cross-origin data theft
2. Check for reflected/wildcard origins on authenticated endpoints
3. Review security headers on API responses: CSP, X-Content-Type-Options,
   Strict-Transport-Security — missing headers aren't critical alone but
   compound with other findings
```

---

## 🕸️ Phase 11 — GraphQL-Specific Testing

```
1. Check if introspection is enabled: query { __schema { types { name } } }
2. Enumerate all queries/mutations/fields from the introspection result
3. Test for BOLA on object-returning queries the same way as REST
4. Test batching/aliasing to bypass rate limits (bundle many queries
   into a single request/alias set)
5. Test deeply nested queries for denial-of-service (query depth abuse)
6. Look for mutations without proper auth checks (e.g. deleteUser,
   updateRole) that aren't exposed in the normal UI flow
```

---

## 🌍 Phase 12 — SSRF & Server-Side Request Flaws

```
1. Identify any endpoint that fetches a URL server-side: webhooks,
   "import from URL", avatar-from-URL, PDF/screenshot generators
2. Test internal targets: http://127.0.0.1, http://169.254.169.254/
   (cloud metadata), http://localhost:PORT, internal hostnames
3. Try bypasses if filtered: decimal IP (2130706433), IPv6 (::1),
   redirects (short URL → internal target), DNS rebinding
```

---

## 🧩 Phase 13 — Misc Lifecycle & Config Flaws

- **Verbose errors** — stack traces, DB errors, or framework version info leaked in 500 responses.
- **Debug endpoints left enabled** — `/actuator`, `/metrics`, `/.env`, `/config`, `/status` exposed in production.
- **Stale tokens after logout** — API tokens/sessions still valid after the user logs out or deletes their account.
- **Webhook signature not verified** — incoming webhooks accepted without validating the signing secret.
- **File upload flaws** — no type/extension validation, path traversal in filename, stored XSS via SVG upload.

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│                API TESTING WORKFLOW                   │
├──────────────────────────────────────────────────────┤
│                                                        │
│  1. 🔍 Recon & Map Every Endpoint (docs/JS/crawl)     │
│            ↓                                          │
│  2. 🔑 Test Authentication (JWT/keys/session)         │
│            ↓                                          │
│  3. 🧱 Test Authorization (BOLA/BFLA, cross-account)  │
│            ↓                                          │
│  4. 📦 Check Mass Assignment & Data Exposure          │
│            ↓                                          │
│  5. 💉 Fuzz for Injection (SQLi/NoSQLi/SSTI/cmd)      │
│            ↓                                          │
│  6. 🔓 Test Rate Limits & Resource Abuse              │
│            ↓                                          │
│  7. 🧠 Probe Business Logic (race conditions, state)  │
│            ↓                                          │
│  8. 🔀 Tamper HTTP Methods & Content-Types            │
│            ↓                                          │
│  9. 🗂️ Check Old Versions & Shadow Endpoints          │
│            ↓                                          │
│ 10. 🌐 Test CORS & Security Headers                   │
│            ↓                                          │
│ 11. 🕸️ Test GraphQL Introspection & Batching          │
│            ↓                                          │
│ 12. 🌍 Test SSRF on URL-Fetching Endpoints             │
│            ↓                                          │
│ 13. 🧩 Check Lifecycle/Config Flaws (debug, tokens)   │
│            ↓                                          │
│ 14. 📝 Document & Report                              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
Endpoint returns an object by ID/reference?
    ├── YES → Swap ID while keeping YOUR auth → BOLA test
    │
    ├── Endpoint looks admin/privileged? → Replay with low-priv token → BFLA test
    │
    ├── Accepts a JSON/form body? → Add extra fields (isAdmin, role) → Mass Assignment
    │
    ├── Response includes more fields than the UI shows? → Excessive Data Exposure
    │
    ├── Repeated requests allowed unlimited? → Brute force / resource abuse
    │
    ├── Multi-step flow (payment, redeem, transfer)? → Race condition / state-skip test
    │
    ├── Fetches a URL server-side? → SSRF test (metadata IP, localhost)
    │
    ├── GraphQL endpoint? → Introspection → enumerate → BOLA on queries/mutations
    │
    └── Nothing above works → Method/Content-Type tampering,
                               old API version, verbose error fuzzing
```

---

### 📚 Resources

- 🔗 [OWASP API Security Top 10](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- 🔗 [PortSwigger — API Testing](https://portswigger.net/web-security/api-testing)
- 🔗 [HackTricks — API Pentesting](https://book.hacktricks.xyz/pentesting-web/api-pentesting)
- Companion doc: `2FA-Bypass.md` for auth-flow-specific attacks

---

<div align="center">

### 🔥 Map the surface. Break the boundary. Own the object.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
