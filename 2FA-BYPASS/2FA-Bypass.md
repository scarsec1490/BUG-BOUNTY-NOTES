# 🔐 2FA Bypass Methodology

> **A complete, structured approach to bypassing Two-Factor / OTP authentication — from recon to logic flaws.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-2FA%20%2F%20OTP%20Bypass-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-Auth%20Flow%20%7C%20Session%20%7C%20Logic-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Burp-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Phase 1 — Flow Mapping & Recon](#-phase-1--flow-mapping--recon)
2. [Phase 2 — Response Manipulation](#-phase-2--response-manipulation)
3. [Phase 3 — Status Code Manipulation](#-phase-3--status-code-manipulation)
4. [Phase 4 — Direct / Referrer-Based Endpoint Access](#-phase-4--direct--referrer-based-endpoint-access)
5. [Phase 5 — Session & Flow Logic Flaws](#-phase-5--session--flow-logic-flaws)
6. [Phase 6 — Token Handling Flaws](#-phase-6--token-handling-flaws)
7. [Phase 7 — Client-Side / Developer Checks](#-phase-7--client-side--developer-checks)
8. [Phase 8 — Header-Based Bypass](#-phase-8--header-based-bypass)
9. [Phase 9 — Brute Force (No Rate Limit)](#-phase-9--brute-force-no-rate-limit)
10. [Phase 10 — Arbitrary / Common Input Bypass](#-phase-10--arbitrary--common-input-bypass)
11. [Phase 11 — CSRF & Clickjacking on 2FA](#-phase-11--csrf--clickjacking-on-2fa)
12. [Phase 12 — Misc Lifecycle Flaws](#-phase-12--misc-lifecycle-flaws)
13. [Summary Workflow](#️-summary-workflow)
14. [Quick Decision Tree](#-quick-decision-tree)

---

## 🔍 Phase 1 — Flow Mapping & Recon

Before touching payloads, map the full auth flow in Burp:

```
1. Login with valid creds → note every request in the chain
2. Identify the 2FA/OTP request endpoint(s)
3. Identify the endpoint reached AFTER successful 2FA
4. Note session tokens / cookies set before vs after 2FA
5. Check any JS files loaded on the 2FA page for hardcoded logic
   (rare, but check main.js / bundle.js for OTP validation client-side)
```

> 💡 **Goal:** know every request in the chain so you can replay, skip, or tamper with any single step.

---

## 🧪 Phase 2 — Response Manipulation

### Boolean Flip

Intercept the OTP verification response and flip the result:

```
HTTP/1.1 404 Not Found
...
{"code": false}
```
→ change to:
```
HTTP/1.1 404 Not Found
...
{"code": true}
```

### Swap Correct/Wrong Response Bodies

```
1. Enter the correct OTP → intercept & capture that response
2. Enter a wrong OTP → intercept the response
3. Replace the wrong-OTP response body with the captured correct-OTP response
```

---

## 🧱 Phase 3 — Status Code Manipulation

```
HTTP/1.1 404 Not Found
...
{"code": false}
```
→ change status line only:
```
HTTP/1.1 200 OK
...
{"code": false}
```

Applies to any 4xx response on the OTP-verify endpoint — flip to `200 OK` and check if the app trusts the status code over the body.

---

## 🔬 Phase 4 — Direct / Referrer-Based Endpoint Access

### Direct Access

```
1. Identify the endpoint that comes after 2FA (e.g. site.com/login/new_password)
2. Try navigating straight to it, skipping site.com/login/otp_verification entirely
```

### Referrer Header Bypass

```
1. If direct access fails, set the Referer header to the 2FA page URL
   (or to the post-2FA authenticated page)
2. This can trick server-side checks that only validate "did the request
   come from the right page" rather than "was 2FA actually completed"
```

---

## 🧠 Phase 5 — Session & Flow Logic Flaws

### Session Permission Confusion

```
1. Using ONE session, start the login flow with your own account
2. Also start the login flow with the victim's account (same session)
3. At the 2FA step, complete 2FA using YOUR account — but do not proceed
4. Switch back to the victim's account flow and try to access the next step
```
> Works when the backend just sets a boolean on the *session* ("2FA passed") rather than binding the pass/fail state to the specific account being authenticated.

### Missing Code-to-Account Binding

No integrity check tying the OTP code to the account it was issued for:

```
POST /2fa/
Host: vuln.com
...
email=attacker@gmail.com&code=382923
```
Replay the same code against the victim:
```
POST /2fa/
Host: vuln.com
...
email=victim@gmail.com&code=382923
```

### Session Not Invalidated on 2FA Enable

Enabling 2FA on an account doesn't expire previously active sessions. If a session was already hijacked (or is vulnerable to a session-timeout issue), it stays valid even after the victim turns 2FA on.

---

## 🔑 Phase 6 — Token Handling Flaws

| Flaw | Description |
|---|---|
| **Code in response** | `POST /req-2fa/` with `email=victim@gmail.com` returns `{"email": "...", "code": "101010"}` directly in the response |
| **Code reusability** | The same OTP code can be submitted more than once and is accepted again |
| **Reusing an old token** | An already-used/expired token from earlier in the session still authenticates |
| **Sharing unused tokens across accounts** | Request a code for your own account, then submit it while authenticating a *different* account |
| **JS file leakage** | Bundled JS occasionally embeds OTP generation/validation logic or hardcoded values (rare, but worth a grep) |

Example — code disclosed in response:
```
POST /req-2fa/
Host: vuln.com
...
email=victim@gmail.com
```
```
HTTP/1.1 200 OK
...
{"email": "victim@gmail.com", "code": "101010"}
```

---

## 🖥️ Phase 7 — Client-Side / Developer Checks

```
1. Right-click the submit/continue button on the OTP page → Inspect
2. Look for a client-side validation function, e.g. checkOTP(event)
3. Open DevTools console and call the function directly with a
   crafted/guessed argument to see if validation logic lives client-side
```

Reference: [OTP Bypass — Developer's Check (shahjerry33)](https://shahjerry33.medium.com/otp-bypass-developers-check-5786885d55c6)

---

## 📡 Phase 8 — Header-Based Bypass

Add spoofed origin/IP headers to the 2FA request to try to satisfy IP-based trust or rate-limit checks:

```
X-Forwarded-For: 127.0.0.1
```

If that doesn't work, cycle through:

```
X-Originating-IP
X-Forwarded-Fo
X-Remote-IP
X-Remote-Addr
X-Client-IP
X-Host
X-Forwared-Host
```

---

## 🔓 Phase 9 — Brute Force (No Rate Limit)

```
1. Send the OTP-verify request to Burp Intruder
2. Set the code parameter as the payload position
3. Use a numeric range (000000–999999, or the code's known length)
4. Check for the absence of:
     - Rate limiting
     - Account lockout after N attempts
     - CAPTCHA on repeated failures
```

---

## 🧬 Phase 10 — Arbitrary / Common Input Bypass

Try submitting non-standard values in the `code` field — some backends have fallback/debug logic that improperly accepts these:

```
code=000000
code=00000
code=null
code=0
code=ASADSas
```

Also test changing the HTTP request method (GET↔POST, etc.) on the verify endpoint, as some frameworks route method variants to different (unvalidated) handlers.

---

## 🛡️ Phase 11 — CSRF & Clickjacking on 2FA

### No CSRF Protection on Disabling 2FA

```
1. Check if the "disable 2FA" endpoint accepts requests without a
   CSRF token, and without re-confirming the current password/OTP
2. If so, craft an auto-submitting CSRF PoC page targeting that endpoint
```

### Clickjacking

```
1. Check if the 2FA-disable page can be framed (missing X-Frame-Options /
   frame-ancestors CSP)
2. If frameable, build an iframe overlay page and lure the victim into
   clicking "disable" without realizing it
```

---

## 🧩 Phase 12 — Misc Lifecycle Flaws

- **2FA disabled on password/email change** — changing the account password or email silently turns 2FA off, with no re-verification required.

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│                 2FA BYPASS WORKFLOW                   │
├──────────────────────────────────────────────────────┤
│                                                        │
│  1. 🔍 Map the Full Auth Flow (Burp)                  │
│            ↓                                          │
│  2. 🧪 Try Response Manipulation (boolean/body swap)  │
│            ↓                                          │
│  3. 🧱 Try Status Code Manipulation (4xx → 200)       │
│            ↓                                          │
│  4. 🔬 Try Direct / Referrer-Based Endpoint Access    │
│            ↓                                          │
│  5. 🧠 Test Session & Cross-Account Flow Logic        │
│            ↓                                          │
│  6. 🔑 Check Token Handling (leak/reuse/share)        │
│            ↓                                          │
│  7. 🖥️ Inspect Client-Side Validation Functions       │
│            ↓                                          │
│  8. 📡 Try Header-Based IP Spoofing                   │
│            ↓                                          │
│  9. 🔓 Brute Force if No Rate Limit                   │
│            ↓                                          │
│ 10. 🧬 Try Arbitrary/Common Codes (000000, null...)   │
│            ↓                                          │
│ 11. 🛡️ Check CSRF/Clickjacking on 2FA Disable         │
│            ↓                                          │
│ 12. 🧩 Check Lifecycle Flaws (password/email change)  │
│            ↓                                          │
│ 13. 📝 Document & Report                              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
OTP verification request identified?
    ├── YES → Intercept response
    │           ├── Result flag in body (true/false) → Response Manipulation
    │           ├── 4xx status on failure → Status Code Manipulation
    │           ├── code visible in ANY response → Token Handling Flaw
    │           └── code accepted for wrong account → Missing Binding Flaw
    │
    ├── Can reach post-2FA page directly? → Direct/Referrer Bypass
    │
    ├── Client-side "checkOTP()"-style function? → Developer's Check
    │
    ├── No rate limit on attempts? → Brute Force
    │
    ├── Disable-2FA endpoint has no CSRF token? → CSRF/Clickjacking
    │
    └── Nothing above works → Try arbitrary inputs (000000/null/0)
                               and header spoofing (X-Forwarded-For)
```

---

### 📚 Resources

- 🔗 [OTP Bypass — Developer's Check](https://shahjerry33.medium.com/otp-bypass-developers-check-5786885d55c6)
- 🔗 [HackTricks — 2FA/OTP Bypass](https://book.hacktricks.xyz/pentesting-web/2fa-bypass)
- Source techniques compiled from: Harsh Bothra and other writeups

---

<div align="center">

### 🔥 Map the flow. Break the binding. Own the session.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
