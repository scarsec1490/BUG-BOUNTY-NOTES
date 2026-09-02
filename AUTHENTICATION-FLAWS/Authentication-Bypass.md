# 🔓 Authentication Bypass Methodology

> **A complete, structured approach to bypassing authentication in web apps & APIs — from forced browsing to chained ATO.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-Authentication%20Bypass-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-Session%20%7C%20SSO%20%7C%20Token%20%7C%20API-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Burp-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Phase 1 — Recon & Flow Mapping](#-phase-1--recon--flow-mapping)
2. [Phase 2 — Forced Browsing & Workflow Skip](#-phase-2--forced-browsing--workflow-skip)
3. [Phase 3 — Parameter Tampering / Privilege Injection](#-phase-3--parameter-tampering--privilege-injection)
4. [Phase 4 — Session-Based Bypasses](#-phase-4--session-based-bypasses)
5. [Phase 5 — Password Reset & Recovery Flaws](#-phase-5--password-reset--recovery-flaws)
6. [Phase 6 — MFA / 2FA Bypass](#-phase-6--mfa--2fa-bypass)
7. [Phase 7 — SSO / SAML / OAuth / OIDC Bypass](#-phase-7--sso--saml--oauth--oidc-bypass)
8. [Phase 8 — Token Bypass (JWT / API Keys)](#-phase-8--token-bypass-jwt--api-keys)
9. [Phase 9 — Protocol & Channel Bypass](#-phase-9--protocol--channel-bypass)
10. [Phase 10 — Parser & Backdoor Abuse](#-phase-10--parser--backdoor-abuse)
11. [Phase 11 — Chained Bypass](#-phase-11--chained-bypass)
12. [Testing Methodology & Tools](#-testing-methodology--tools)
13. [Summary Workflow](#️-summary-workflow)
14. [Quick Decision Tree](#-quick-decision-tree)

---

## 🔍 Phase 1 — Recon & Flow Mapping

Before tampering with anything, map every auth-related endpoint and state transition:

```
1. Log in with a valid account → capture every request in Burp
2. Note ALL protected URLs/endpoints hit post-login
3. Note session/token issuance points (login, 2FA, SSO callback)
4. Log out → re-test the same URLs directly
5. Identify alternate channels: /web/login vs /api/login vs mobile endpoints
```

> 💡 **Goal:** a full map of the auth state machine — every step, every token, every channel — before picking a bypass angle.

---

## 🧪 Phase 2 — Forced Browsing & Workflow Skip

### Direct URL Access

```
1. Log in → capture protected URLs
2. Log out → access directly
3. Try common paths: /admin, /dashboard, /api/user
```
**Impact:** Unauthorized access to sensitive areas.

### Multi-Step Login / 2FA Skip

```
1. Complete login up to the 2FA step
2. Note the post-2FA redirect URL
3. Navigate directly to that URL without completing 2FA
```
**Impact:** Complete authentication bypass.

---

## 🧠 Phase 3 — Parameter Tampering / Privilege Injection

```
1. Capture login/profile-update requests
2. Inject or modify privilege flags: isAdmin=true, role=admin, admin=1
3. Replay the request → check for elevated access
```
**Impact:** Privilege escalation to admin.

---

## 🔑 Phase 4 — Session-Based Bypasses

| Technique | How It Works | Steps |
|---|---|---|
| **Session Fixation** | Attacker sets a session ID before the victim logs in, then reuses it post-login | 1) Get an unauthenticated session ID 2) Force the victim to log in using it 3) Reuse the session as the attacker |
| **Session Replay After Logout / PW Change** | Old cookies/tokens remain valid after logout or password reset | 1) Login, capture cookie/token 2) Logout or change password 3) Replay the old session |
| **Orphaned / Zombie Sessions** | Sessions aren't invalidated on role change or account deletion | 1) Login, get token 2) Delete the account or downgrade its role 3) Reuse the old token |
| **Race Condition in Login/Token Issuance** | Concurrent requests bypass limits or checks | 1) Fire multiple simultaneous login/token requests (Turbo Intruder) 2) Look for over-limit success |
| **Cookie Attribute Misconfig** | Missing `Secure` / `HttpOnly` / `SameSite` flags enable theft | 1) Check cookie flags in response headers 2) Steal via XSS/MITM if flags are missing 3) Replay elsewhere |

**Impact:** Account takeover, persistent post-logout access, session hijacking.

---

## 🛡️ Phase 5 — Password Reset & Recovery Flaws

### Reset Token Reuse / Predictability

```
1. Request a password reset → use the token once
2. Try reusing the same token again
3. Check if tokens are sequential or time-based → guess a valid one
```

### Broken Recovery Flow

```
1. Trigger the account-recovery flow
2. Tamper with the user/email parameter mid-flow
3. Attempt to complete reset without proper identity verification
```
**Impact:** Repeated or one-shot account takeover via recovery.

---

## 🔓 Phase 6 — MFA / 2FA Bypass

> For the full breakdown of OTP-specific techniques (response manipulation, status codes, token binding, etc.) see the dedicated **2FA Bypass Methodology**. Summary below:

| Technique | How It Works | Steps |
|---|---|---|
| **Response Manipulation** | Client trusts a success response; tamper failure → success | 1) Enter a wrong OTP 2) Intercept and change the code/body to a success value 3) Forward → access granted |
| **Rate Limit / Enumeration Abuse** | No rate limit on OTP submission | 1) Trigger an OTP 2) Send many codes rapidly 3) Test null/empty OTP values |
| **MFA Fatigue / Push Bombing** | Repeated push prompts wear the victim down into approving one | 1) Attempt logins repeatedly 2) Observe push notification spam 3) Check if an accidental approval grants access |

**Impact:** Client-side 2FA illusion, OTP cracking, social-engineered MFA defeat.

---

## 🌐 Phase 7 — SSO / SAML / OAuth / OIDC Bypass

### SAML Parser Differential

```
1. Intercept the SAML response
2. Exploit XML/assertion parser inconsistencies (e.g. duplicate attributes,
   ruby-saml / PHP parser diffs)
3. Forge an assertion for a privileged/admin identity
```
**Impact:** SSO-wide account takeover (see 2025 Ruby-SAML class of exploits).

### OAuth / OIDC Redirect & Code Misuse

```
1. Intercept the OAuth authorization flow
2. Tamper with redirect_uri, reuse an authorization code, or check for
   missing `state` parameter (CSRF on the OAuth flow)
3. Steal or replay tokens
```
**Impact:** OAuth login bypass, token theft.

### CAS / SSO Ticket Replay

```
1. Capture a CAS service ticket
2. Replay it against a different connected service
```
**Impact:** Cross-service account takeover.

### Multi-Tenant SSO Bypass

```
1. Locate the tenant_id parameter in the SAML/OAuth flow
2. Swap it for a different tenant's ID
3. Check for cross-tenant access
```
**Impact:** SaaS tenant-isolation break.

---

## 🧬 Phase 8 — Token Bypass (JWT / API Keys)

### JWT Manipulation

```
1. Decode the JWT (jwt.io / jwt_tool)
2. Try alg=none, a weak/guessable HMAC secret, or kid-header injection
3. Forge the signature and replay
```
**Impact:** Unsigned/forged token acceptance.

### API Key / Token Leak & Reuse

```
1. Search client-side JS/mobile app code for hardcoded API keys
2. Check logs/URLs for tokens leaked via GET params or Referer headers
3. Reuse the token in an unauthorized context (no binding to origin/user)
```
**Impact:** API authentication bypass.

---

## 🔀 Phase 9 — Protocol & Channel Bypass

### HTTP Method Switching

```
1. Confirm POST /login enforces authentication
2. Retry the same endpoint with GET (or another verb)
3. Check if the method-switched request is processed without auth
```

### Alternate Path / Channel Bypass

```
1. Compare enforcement between channels: /api/login vs /web/login,
   mobile endpoints vs web endpoints, legacy vs current API versions
2. Identify a channel where auth is inconsistently enforced
```

### GraphQL / Batching Auth Bypass

```
1. Send a batched GraphQL query/mutation
2. Mix an authenticated-required operation with unauthenticated ones
   in the same batch
3. Check whether the batch executes operations without per-op auth checks
```

**Impact:** Inconsistent auth enforcement, mixed auth execution.

---

## 🕵️ Phase 10 — Parser & Backdoor Abuse

### Null Byte / Canonicalization Bypass

```
1. Attempt login with a null byte in the username/email, e.g. user%00@evil.com
2. Check if backend parsing/validation is fooled by the malformed input
```

### Backdoor / Debug Auth Endpoints

```
1. Fuzz for leftover debug endpoints and parameters:
   /test/login, /debug/auth, ?bypass=1, ?admin=true
2. Try common developer-leftover backdoors
```

**Impact:** Parser confusion, leftover dev-access exposure.

---

## 🔗 Phase 11 — Chained Bypass

```
1. Combine an auth bypass with a secondary flaw: IDOR, mass assignment,
   business-logic flaw
2. Escalate from anonymous/low-privilege to admin using the chain
```
**Impact:** Critical, often full account/system takeover.

---

## 🛠️ Testing Methodology & Tools

### Essential Tools

```
• Burp Suite (Proxy, Repeater, Intruder, Turbo Intruder)
• OWASP ZAP
• Postman / Insomnia
• jwt.io + jwt_tool
• SAML Raider (Burp extension)
• Custom scripts (Python requests)
```

### Best Practices

```
✅ Use multiple accounts (victim + attacker)
✅ Test every auth flow: login, 2FA, SSO, OAuth, API
✅ Intercept EVERY request — cookies, headers, bodies
✅ Re-test after state changes (logout, password change, role change)
✅ Check alternate channels (web / mobile / API / legacy)
✅ Document PoCs with clear before/after access evidence
```

### Common Indicators to Watch For

```
🚩 Direct access to /dashboard without login
🚩 Old tokens still valid after logout
🚩 Tampered parameters grant elevated access
🚩 Inconsistent 401/403 behavior across endpoints
🚩 No rate limiting on OTP or password-reset requests
```

---

## ⚔️ Summary Workflow

```
┌────────────────────────────────────────────────────────┐
│           AUTHENTICATION BYPASS WORKFLOW               │
├────────────────────────────────────────────────────────┤
│                                                          │
│  1. 🔍 Map the Full Auth Flow (Burp)                    │
│            ↓                                            │
│  2. 🧪 Try Forced Browsing / Workflow Skip              │
│            ↓                                            │
│  3. 🧠 Try Parameter Tampering (role/privilege flags)   │
│            ↓                                            │
│  4. 🔑 Test Session-Based Flaws (fixation/replay/race)  │
│            ↓                                            │
│  5. 🛡️ Test Password Reset & Recovery Flow              │
│            ↓                                            │
│  6. 🔓 Test MFA/2FA Bypass Vectors                      │
│            ↓                                            │
│  7. 🌐 Test SSO/SAML/OAuth/OIDC Flow                    │
│            ↓                                            │
│  8. 🧬 Test JWT / API Key Handling                      │
│            ↓                                            │
│  9. 🔀 Test Protocol & Channel Inconsistencies          │
│            ↓                                            │
│ 10. 🕵️ Test Parser Confusion & Backdoors                │
│            ↓                                            │
│ 11. 🔗 Chain With Secondary Flaws (IDOR, mass assign)   │
│            ↓                                            │
│ 12. 📝 Document & Report                                │
│                                                          │
└────────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
Can you reach a protected page/endpoint without logging in?
    ├── YES → Forced Browsing / Direct URL Access confirmed
    │
    └── NO → Is there a multi-step flow (login → 2FA → SSO)?
                ├── YES → Try skipping to the post-step URL directly
                │           (Workflow Step Bypass)
                └── NO → Inspect session/token handling
                            ├── Old token still valid post-logout? → Session Replay
                            ├── Session reused across accounts? → Session Fixation
                            ├── JWT present? → Decode & test alg=none / weak sig
                            ├── SSO/SAML/OAuth in flow? → Test parser diffs,
                            │                              redirect_uri, state param
                            ├── Password reset available? → Test token reuse/predictability
                            └── Nothing above works → Try parameter tampering
                                                       (role=admin, isAdmin=true)
                                                       and method switching (GET vs POST)
```

---

<div align="center">

### 🔥 Map the flow. Break the binding. Own the session.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
