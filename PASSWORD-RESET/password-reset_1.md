# PASSWORD RESET & ACCOUNT MANAGEMENT BUSINESS LOGIC BUGS
---

## 1️⃣ PASSWORD RESET TOKEN LEAKAGE
**How it works:** Reset tokens exposed in URLs, response bodies, logs, or via side-channel attacks.

**Steps to Find:**
1. Request password reset for your account
2. Check URL parameters for token exposure (?token=)
3. Inspect HTTP responses for tokens in JSON/HTML
4. Search server logs if accessible
5. Check if tokens appear in analytics/telemetry
6. Test timing attacks on token validation

**Impact:** Account takeover, token theft, authentication bypass

---

## 2️⃣ RESET TOKEN PREDICTABILITY
**How it works:** Tokens are generated using weak algorithms (timestamp, sequential numbers, user attributes).

**Steps to Find:**
1. Request multiple reset tokens for the same user
2. Analyze token patterns (length, charset, structure)
3. Check if tokens contain encoded user data (base64 email)
4. Test sequential token generation
5. Attempt to brute-force token space
6. Check token expiration and reuse

**Impact:** Account takeover via token prediction/brute-force

---

## 3️⃣ TOKEN EXPIRATION BYPASS
**How it works:** Expired tokens remain valid, or expiration isn't properly enforced.

**Steps to Find:**
1. Request password reset token
2. Wait beyond stated expiration time (5min, 1hr, 24hr)
3. Attempt to use expired token
4. Reuse old tokens after password change
5. Test if expiration is client-side only
6. Check server time vs client time mismatches

**Impact:** Unlimited time window for account takeover

---

## 4️⃣ RESET TOKEN REUSE
**How it works:** Tokens remain valid after use, allowing multiple password changes.

**Steps to Find:**
1. Request password reset token
2. Use token to change password
3. Attempt to reuse same token for another change
4. Try using token on different accounts
5. Test token invalidation after successful use
6. Check if token works after account lockout

**Impact:** Account instability, denial of service, persistent backdoor

---

## 5️⃣ PASSWORD RESET HIJACKING
**How it works:** Reset functionality allows attackers to change where reset links/emails are sent.

**Steps to Find:**
1. Initiate password reset
2. Intercept request containing email parameter
3. Change email to attacker-controlled address
4. Check if verification email sent to new address
5. Test with different email formats/domains
6. Verify if confirmation required for email change

**Impact:** Complete account takeover, email interception

---

## 6️⃣ ACCOUNT VERIFICATION BYPASS
**How it works:** Email/phone verification can be skipped or forged.

**Steps to Find:**
1. Register new account with unverified email/phone
2. Attempt to access privileged features without verification
3. Intercept verification request
4. Change verification status parameter (verified=true)
5. Test verification code brute-force (4-6 digit codes)
6. Check if verification persists after email change

**Impact:** Fake account creation, spam, fraud

---

## 7️⃣ PASSWORD RESET ON UNREGISTERED ACCOUNTS
**How it works:** System reveals whether email/username exists via reset functionality.

**Steps to Find:**
1. Enter valid email, check response/time
2. Enter invalid email, compare response
3. Test timing differences in email processing
4. Check error messages for existence clues
5. Test bulk email enumeration via reset
6. Verify if rate limiting prevents enumeration

**Impact:** User enumeration, reconnaissance, targeted attacks

---

## 8️⃣ WEAK RESET QUESTION EXPLOITATION
**How it works:** Security questions are guessable, enumerable, or bypassable.

**Steps to Find:**
1. Identify reset question options
2. Test common answers ("blue", "dog", "mother's maiden name")
3. Check if answers are case-sensitive
4. Attempt to skip questions entirely
5. Test answer brute-force (no lockout)
6. Verify if questions/answers stored securely

**Impact:** Account takeover via social engineering

---

## 9️⃣ PASSWORD CHANGE WITHOUT OLD PASSWORD
**How it works:** Password change functionality doesn't require current password verification.

**Steps to Find:**
1. Login with low-privilege account
2. Find password change endpoint
3. Attempt to change password without providing current password
4. Test with other users' IDs via parameter tampering
5. Check if session token alone is sufficient
6. Verify CSRF protection on password change

**Impact:** Account takeover via CSRF or session hijacking

---

## 🔟 ACCOUNT MERGER/UNLINKING VULNERABILITY
**How it works:** Linked accounts (Google, Facebook, SSO) can be unlinked improperly.

**Steps to Find:**
1. Link external account to primary account
2. Find unlink/remove account functionality
3. Attempt to unlink while maintaining access
4. Test if unlinking creates orphaned accounts
5. Check privilege retention after unlink
6. Verify re-linking with different accounts

**Impact:** Account separation failure, privilege retention

---

## 1️⃣1️⃣ PASSWORD RESET CSRF
**How it works:** Password reset requests lack CSRF protection, allowing attackers to reset victims' passwords.

**Steps to Find:**
1. Identify password reset form
2. Check for CSRF tokens or same-origin validation
3. Create malicious page that auto-submits reset
4. Test with authenticated victim sessions
5. Verify if confirmation required (current password)
6. Check referrer/Origin header validation

**Impact:** Account takeover via malicious website

---

## 1️⃣2️⃣ PASSWORD STRENGTH BYPASS
**How it works:** Client-side password validation can be bypassed, allowing weak passwords.

**Steps to Find:**
1. Attempt to set weak password via UI (note error)
2. Intercept password change request
3. Modify to weak password (123456, password)
4. Bypass complexity requirements
5. Test minimum length enforcement
6. Check server-side vs client-side validation

**Impact:** Weak credential security, brute-force vulnerability

---

## 1️⃣3️⃣ ACCOUNT RECOVERY EMAIL CHANGING
**How it works:** Recovery email can be changed without verification or notification.

**Steps to Find:**
1. Locate recovery email settings
2. Attempt to change without verifying new email
3. Test if old recovery email receives notification
4. Check if primary email notified of change
5. Attempt to set non-existent email as recovery
6. Verify confirmation requirements

**Impact:** Account takeover via recovery email hijacking

---

## 1️⃣4️⃣ PASSWORD HISTORY EXPLOITATION
**How it works:** Password history checks are weak or can be bypassed.

**Steps to Find:**
1. Change password multiple times
2. Attempt to reuse recent passwords
3. Test history depth (last 3, 5, 10 passwords)
4. Bypass via password variations (Password1!, Password2!)
5. Check if history applies to reset vs change
6. Verify history stored securely

**Impact:** Weak password rotation, security policy bypass

---

## 1️⃣5️⃣ ACCOUNT LOCKOUT BYPASS
**How it works:** Lockout mechanisms can be bypassed via parameter manipulation or alternative endpoints.

**Steps to Find:**
1. Trigger account lockout with failed attempts
2. Try different login endpoints (mobile API, legacy API)
3. Change IP address or user agent
4. Use password reset to unlock account
5. Test lockout counter reset mechanisms
6. Check if lockout is client-side enforced

**Impact:** Brute-force attacks, denial of service to legitimate users

---

## 1️⃣6️⃣ SESSION PERSISTENCE AFTER PASSWORD CHANGE
**How it works:** Old sessions remain active after password change, allowing continued access.

**Steps to Find:**
1. Login and obtain session token
2. Change password via another browser/tab
3. Return to original session, attempt privileged action
4. Check if session invalidated globally
5. Test mobile vs web session handling
6. Verify API tokens after password change

**Impact:** Session hijacking persistence, security policy bypass

---

## 1️⃣7️⃣ MULTI-FACTOR BYPASS VIA RESET
**How it works:** Password reset doesn't require MFA, allowing 2FA bypass.

**Steps to Find:**
1. Enable MFA on account
2. Initiate password reset
3. Check if reset requires MFA verification
4. Test if reset disables MFA temporarily
5. Verify MFA status after password change
6. Test backup code usage during reset

**Impact:** Complete MFA bypass, account takeover

---

## 1️⃣8️⃣ ACCOUNT TAKEOVER VIA UNVERIFIED PARAMETERS
**How it works:** User-controllable parameters in account management aren't properly validated.

**Steps to Find:**
1. Map all account management endpoints
2. Identify parameters like user_id, account_id, email
3. Modify to other users' identifiers
4. Test privilege escalation parameters (role, isAdmin)
5. Check for mass assignment vulnerabilities
6. Verify server-side authorization checks

**Impact:** Horizontal/vertical privilege escalation, account takeover

---

## 1️⃣9️⃣ PASSWORD RESET FLOODING
**How it works:** Unlimited password reset requests can be sent, flooding user's email.

**Steps to Find:**
1. Test rate limiting on reset requests
2. Send continuous reset requests to target email
3. Check if system blocks or delays emails
4. Test with different email formats/case variations
5. Verify email queue processing
6. Check for denial-of-service protections

**Impact:** Email flooding, denial of service, user annoyance

---

## 2️⃣0️⃣ ACCOUNT DEACTIVATION/RECOVERY FLAWS
**How it works:** Deactivated accounts can be recovered with insufficient verification.

**Steps to Find:**
1. Deactivate account through settings
2. Attempt to reactivate with weak verification
3. Check if recovery window exists
4. Test reactivation with old credentials
5. Verify data restoration after reactivation
6. Check for privilege retention

**Impact:** Unauthorized account recovery, data exposure

---

## 🔧 TESTING METHODOLOGY

### Phase 1: Reconnaissance
1. **Map Authentication Flow:** Login, registration, reset, recovery
2. **Identify Endpoints:** /reset, /forgot, /change-password, /verify
3. **Document Parameters:** Tokens, emails, user IDs, verification codes

### Phase 2: Functional Testing
1. **Happy Path:** Test legitimate flows
2. **Edge Cases:** Expired tokens, used tokens, invalid inputs
3. **State Testing:** Session persistence, concurrent operations

### Phase 3: Security Testing
1. **Token Analysis:** Predictability, leakage, reuse
2. **Authorization Testing:** Horizontal/vertical privilege escalation
3. **Input Validation:** Bypass client-side checks

### Tools:
- **Burp Suite:** Intercept, repeater, intruder, sequencer
- **Browser DevTools:** Monitor network, modify requests
- **Custom Scripts:** Token generation analysis, brute-force
- **Email Testing:** Temp mail services, mail servers

---

## 🚨 RED FLAGS & COMMON PATTERNS

### High-Risk Indicators:
1. **Tokens in URLs:** Visible in browser history, logs, referrers
2. **Predictable Patterns:** Sequential, time-based, user-dependent tokens
3. **Lack of Expiration:** Tokens work indefinitely
4. **No Rate Limiting:** Unlimited reset requests
5. **Client-Side Validation:** Rules bypassed via proxy
6. **Information Leakage:** Different responses for valid/invalid users
7. **Missing Confirmation:** No email/notification for sensitive changes
8. **Weak Verification:** 4-digit codes, security questions
9. **Session Issues:** Old sessions persist after password change
10. **Cross-User Access:** Parameter tampering allows access to other accounts

