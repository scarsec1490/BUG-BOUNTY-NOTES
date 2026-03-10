AUTHENTICATION BYPASS VULNERABILITIES FOR WEB APPS & APIs 

1️⃣ FORCED BROWSING / DIRECT URL ACCESS
How it works: Protected pages/endpoints accessible without login by guessing URLs.

Steps to Find:
1. Log in → capture protected URLs
2. Log out → access directly
3. Try /admin, /dashboard, /api/user

Impact: Unauthorized access to sensitive areas

---

2️⃣ WORKFLOW STEP BYPASS (Multi-Step Login Skip)
How it works: Skipping login/2FA steps by direct access to post-auth URLs.

Steps to Find:
1. Complete login up to 2FA
2. Note post-2FA redirect URL
3. Access directly without 2FA

Impact: Complete auth bypass

---

3️⃣ PARAMETER TAMPERING (Role/Flag Injection)
How it works: Modify params like isAdmin=true, role=admin in requests.

Steps to Find:
1. Capture login/update requests
2. Add/inject privilege flags
3. Replay → check elevated access

Impact: Privilege escalation to admin

---

4️⃣ SESSION FIXATION
How it works: Attacker sets session ID before login; victim logs in → attacker hijacks.

Steps to Find:
1. Get unauth session
2. Force victim to login with it
3. Use session post-login

Impact: Account takeover

---

5️⃣ SESSION REPLAY AFTER LOGOUT / PASSWORD CHANGE
How it works: Old sessions/tokens remain valid after logout or pw reset.

Steps to Find:
1. Login → capture cookie/token
2. Logout / change pw
3. Replay old session

Impact: Persistent access post-logout

---

6️⃣ PASSWORD RESET TOKEN REUSE / PREDICTABILITY
How it works: Reset tokens reusable, predictable, or not invalidated.

Steps to Find:
1. Request reset → use token once
2. Reuse same token
3. Guess tokens (sequential/time-based)

Impact: Repeated ATO

---

7️⃣ MFA / 2FA BYPASS VIA RESPONSE MANIPULATION
How it works: Client trusts success response; tamper 401 → 200.

Steps to Find:
1. Enter wrong OTP
2. Intercept → change code/body to success
3. Forward → access granted

Impact: Client-side 2FA illusion

---

8️⃣ MFA BYPASS VIA RATE LIMIT / ENUMERATION ABUSE
How it works: No rate limit on OTP → brute force or reuse.

Steps to Find:
1. Trigger OTP
2. Send many codes rapidly
3. Test null/empty OTP

Impact: OTP cracking

---

9️⃣ MFA FATIGUE / PUSH BOMBING BYPASS
How it works: Spam push notifications → victim approves accidentally.

Steps to Find:
1. Attempt logins repeatedly
2. Observe push spam
3. Check if approval grants access

Impact: Social engineering MFA defeat

---

10️⃣ SAML / SSO PARSER DIFFERENTIAL BYPASS
How it works: XML/Assertion parser inconsistencies allow forged SAML responses.

Steps to Find:
1. Intercept SAML response
2. Exploit ruby-saml/PHP diffs (e.g., duplicate attributes)
3. Forge admin assertion

Impact: SSO-wide ATO (2025 Ruby-SAML exploits)

---

11️⃣ OAUTH / OPENID CONNECT REDIRECT / CODE MISUSE
How it works: Redirect URI manipulation, code reuse, or state missing.

Steps to Find:
1. Intercept OAuth flow
2. Tamper redirect_uri or code
3. Steal tokens

Impact: OAuth login bypass

---

12️⃣ JWT / TOKEN MANIPULATION (None Alg, Weak Sig)
How it works: alg=none, weak secret, kid header injection.

Steps to Find:
1. Decode JWT
2. Change alg=none or forge sig
3. Replay

Impact: Unsigned token acceptance

---

13️⃣ API KEY / TOKEN IN URL / HEADER LEAK + REUSE
How it works: Tokens exposed in logs/URLs; reusable without binding.

Steps to Find:
1. Find API key in client code
2. Use in unauthorized context

Impact: API auth bypass

---

14️⃣ ALTERNATE PATH / CHANNEL BYPASS
How it works: Mobile/API/legacy endpoints lack auth enforced on web.

Steps to Find:
1. Test /api/login vs /web/login
2. Bypass on one channel

Impact: Inconsistent enforcement

---

15️⃣ BROKEN PASSWORD RECOVERY FLOW
How it works: Recovery bypasses auth (e.g., security questions weak/no rate limit).

Steps to Find:
1. Trigger recovery
2. Tamper user/email
3. Reset without verification

Impact: ATO via recovery

---

16️⃣ HTTP METHOD SWITCHING BYPASS
How it works: GET bypasses auth while POST requires it.

Steps to Find:
1. Test POST /login → required
2. Switch to GET → accepted

Impact: Method-based auth leak

---

17️⃣ ORPHANED / ZOMBIE SESSIONS
How it works: Sessions not invalidated on role change/account delete.

Steps to Find:
1. Login → get token
2. Delete account / downgrade role
3. Use old token

Impact: Post-deletion access

---

18️⃣ GRAPHQL / BATCHING AUTH BYPASS
How it works: Batch queries ignore auth on some operations.

Steps to Find:
1. Send batched mutations
2. Include unauth ops

Impact: Mixed auth execution

---

19️⃣ CAS / SSO TICKET REPLAY
How it works: Service tickets reusable or not validated.

Steps to Find:
1. Capture CAS ticket
2. Replay on different services

Impact: Cross-service ATO

---

20️⃣ COOKIE ATTRIBUTE MISCONFIG (Secure/HTTPOnly/SameSite)
How it works: Missing flags → cookie theft → session bypass.

Steps to Find:
1. Check cookie flags
2. Steal via XSS/MITM
3. Replay

Impact: Session hijacking

---

21️⃣ NULL BYTE / CANONICALIZATION BYPASS
How it works: Null bytes in username/password fool checks.

Steps to Find:
1. Login with user%00@evil.com
2. Check if bypasses

Impact: Parser confusion

---

22️⃣ RACE CONDITION IN LOGIN / TOKEN ISSUANCE
How it works: Concurrent logins bypass limits/checks.

Steps to Find:
1. Send multiple login requests
2. Use Turbo Intruder

Impact: Over-limit success

---

23️⃣ BACKDOOR / DEBUG AUTH ENDPOINTS
How it works: Leftover /test/login or ?bypass=1 endpoints.

Steps to Find:
1. Fuzz for debug params
2. Try common backdoors

Impact: Dev leftover access

---

24️⃣ MULTI-TENANT SSO BYPASS
How it works: Tenant ID tampering in SSO flows.

Steps to Find:
1. Switch tenant_id in SAML/OAuth
2. Access cross-tenant

Impact: SaaS isolation break

---

25️⃣ CHAINED BYPASS (Auth + Other Flaws)
How it works: Auth bypass + IDOR/mass-assignment → full ATO.

Steps to Find:
1. Combine with privilege bugs
2. Escalate from anon/low to admin

Impact: Critical chains

TESTING METHODOLOGY
===================

Essential Tools:
• Burp Suite (Proxy, Repeater, Intruder, Turbo Intruder)
• OWASP ZAP
• Postman/Insomnia
• jwt.io + jwt_tool
• SAML Raider / Burp extensions
• Custom scripts (Python requests)

Best Practices:
• Multiple accounts (victim/attacker)
• Test all auth flows: login, 2FA, SSO, OAuth, API
• Intercept EVERY request (cookies, headers, bodies)
• Test post-state-change (logout, pw change)
• Check alternate channels (web/mobile/API)
• Document PoC with before/after access

Common Indicators:
• Direct access to /dashboard without login
• Old tokens valid after logout
• Tampered params grant access
• Inconsistent 401/403 errors
• No rate limiting on OTP/reset
