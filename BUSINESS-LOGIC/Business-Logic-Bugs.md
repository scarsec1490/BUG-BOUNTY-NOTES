# 🧩 Business Logic Bug Hunting Methodology

> **A complete, structured approach to finding business logic flaws — from price tampering to workflow bypass.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-Business%20Logic-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-Pricing%20%7C%20Workflow%20%7C%20State-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Burp-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Phase 1 — Recon & Flow Mapping](#-phase-1--recon--flow-mapping)
2. [Phase 2 — Price & Calculation Manipulation](#-phase-2--price--calculation-manipulation)
3. [Phase 3 — Discount / Coupon / Gift Card Abuse](#-phase-3--discount--coupon--gift-card-abuse)
4. [Phase 4 — Limit & Threshold Bypass](#-phase-4--limit--threshold-bypass)
5. [Phase 5 — Workflow & Step Bypass](#-phase-5--workflow--step-bypass)
6. [Phase 6 — Race Condition Exploitation](#-phase-6--race-condition-exploitation)
7. [Phase 7 — Parameter Tampering & Forced Browsing](#-phase-7--parameter-tampering--forced-browsing)
8. [Phase 8 — Order & Refund Abuse](#-phase-8--order--refund-abuse)
9. [Phase 9 — Inventory & Resource Abuse](#-phase-9--inventory--resource-abuse)
10. [Phase 10 — Account Enumeration & Subscription Logic](#-phase-10--account-enumeration--subscription-logic)
11. [Testing Methodology & Tools](#-testing-methodology--tools)
12. [Summary Workflow](#️-summary-workflow)
13. [Quick Decision Tree](#-quick-decision-tree)

---

## 🔍 Phase 1 — Recon & Flow Mapping

Map the full application flow before touching any value:

```
1. Walk through every multi-step process end-to-end
   (checkout, registration, subscription, withdrawal, upload)
2. Capture EVERY request in Burp — note which params control
   price, quantity, role, state, and step transitions
3. Identify where validation appears to happen: client-side
   (hidden fields, JS) vs server-side (proxy-verify each one)
4. Note documented limits/thresholds (investment caps, discount
   rules, upload quotas) from docs/UI error messages
```

> 💡 **Goal:** know exactly which values the client controls and which the server actually re-validates — that gap is where business logic bugs live.

---

## 💰 Phase 2 — Price & Calculation Manipulation

### Negative Price / Quantity

```
1. Identify price/quantity parameters in the checkout flow
2. Intercept the request in Burp
3. Set price to a negative value (e.g., -999)
4. Set quantity to a negative integer
5. Submit → check if the transaction processes at all,
   and whether the user ends up credited money
```

### Client-Side Price Manipulation

```
1. Inspect HTML source for hidden price fields
2. Modify the value via DevTools or intercept the POST request
3. Change price=100 → price=1 (or 0)
4. Complete the transaction and check what's actually charged
```

### Integer Overflow / Underflow

```
1. Identify numeric input fields (quantity, amount)
2. Test boundary values: 2147483647 (32-bit max), and one above it
3. Test values that wrap to negative on overflow
4. Try decimals where an integer is expected
5. Check the resulting calculation for anomalies
```

### Formula Injection in Calculations

```
1. Locate any field that feeds into a price calculation
2. Input a mathematical expression (e.g., "1+1") instead of a number
3. Try division-by-zero and negative multipliers
4. Check if the backend evaluates the input rather than
   treating it as a plain number
```

**Impact:** Financial loss, free/negative-cost products, incorrect charges, system crashes.

---

## 🎟️ Phase 3 — Discount / Coupon / Gift Card Abuse

### Coupon Stacking

```
1. Add items until the discount threshold is met
2. Apply the discount/coupon
3. Remove items from the cart after the discount is applied
4. Complete the purchase with the discount on the now-smaller order
5. Try applying multiple expired coupons together
6. Send concurrent coupon-redemption requests
```

### Bulk Discount Exploitation

```
1. Identify the bulk-discount threshold
2. Add items to reach it, apply the discount
3. Remove items below the threshold, check if the discount persists
4. Try splitting one large order into several to abuse the tiering
```

### Gift Card / Credit Abuse

```
1. Obtain a valid gift card / credit code
2. Apply it to one purchase, then try applying the SAME code
   to a second, unrelated order
3. Test partial redemptions and check balance tracking accuracy
4. Try to push the balance negative
```

**Impact:** Revenue loss, discount abuse, financial fraud.

---

## 📊 Phase 4 — Limit & Threshold Bypass

```
1. Find documented investment/transaction/spending limits
2. Attempt to exceed the limit via the UI — note the error shown
3. Intercept the underlying request in Burp
4. Locate the amount/limit parameter
5. Modify it to exceed the documented limit
6. Submit → check if the server enforces the limit independently
   of the UI
```
**Impact:** Risk-management failure, regulatory exposure, financial loss.

---

## 🔀 Phase 5 — Workflow & Step Bypass

### Generic Multi-Step Skip

```
1. Identify multi-step workflows: checkout, registration, 2FA
2. Complete step 1, capture the request/response
3. Jump directly to the final-step URL
4. Skip payment/verification steps entirely
5. Load the confirmation page directly
6. Check if the workflow completes without the skipped step
```

### 2FA Not Re-Validated Post-Login

```
1. Start login with valid credentials
2. Reach the 2FA verification page
3. Note the post-2FA destination URL
4. Navigate directly to that destination, skipping 2FA
5. Check whether the session already grants access
```
> See the dedicated **2FA Bypass Methodology** for the full OTP-specific technique set.

### Session Fixation Across State Transitions

```
1. Start a workflow in one state/role (e.g., low-privilege account)
2. Capture the session token
3. Change context — switch account, elevate role, change permission
4. Reuse the OLD session token in the new context
5. Check if authorization is properly revalidated, or if the
   stale token still carries the old (or worse, unrestricted) access
```

**Impact:** Authentication bypass, payment bypass, privilege escalation, unauthorized data exposure.

---

## ⚡ Phase 6 — Race Condition Exploitation

```
1. Identify critical, state-changing operations: withdrawals,
   redemptions, coupon use, inventory decrement
2. Send one legitimate request first to confirm normal behavior
3. Use Turbo Intruder (or a custom script) to fire multiple
   concurrent identical requests
4. Check if ALL of them succeed despite a single-use/limit constraint
5. Verify the resulting account balance or inventory count
```
**Impact:** Double spending, overdrafts, inventory overselling, unlimited redemptions.

---

## 🧠 Phase 7 — Parameter Tampering & Forced Browsing

### Role / Permission Parameter Tampering

```
1. Capture requests containing role/permission indicators
   (role=user, isAdmin=false)
2. Modify to an elevated value (role=admin, isAdmin=true)
3. Change user-ID parameters to reference other accounts
4. Replay against restricted resources and check the response
```

### Forced Browsing to Admin Functions

```
1. Map application endpoints and URL patterns
2. Identify admin-like paths: /admin, /dashboard, /internal
3. Access them directly with a low-privilege (or no) account
4. Try different HTTP methods (GET, POST, PUT, DELETE) on each
5. Check for exposed directory listings
6. Confirm whether authorization is actually enforced server-side
```

**Impact:** Privilege escalation, horizontal/vertical authorization bypass, full system compromise.

---

## 📦 Phase 8 — Order & Refund Abuse

### Refund / Return Abuse

```
1. Complete a legitimate purchase
2. Request a refund through the normal flow
3. Capture and REPLAY the same refund request
4. Check for duplicate-refund validation
5. Try refunding an already-refunded order
6. Try cancelling an order that has already shipped
```

### Order Modification After Approval

```
1. Place and get an order approved
2. Capture the order-confirmation request
3. Locate the order-modification endpoint
4. Attempt to modify items/quantities on the already-approved order
5. Check if the modified order is processed as-is, bypassing
   the approval that was given for the original contents
```

**Impact:** Financial loss, inventory discrepancies, fulfillment fraud.

---

## 📥 Phase 9 — Inventory & Resource Abuse

### Inventory Reservation Without Payment

```
1. Add high-demand items to the cart
2. Abandon the cart without completing purchase
3. Check whether the inventory stays reserved/locked
4. Add maximum quantities and abandon repeatedly
5. Test the reservation timeout mechanism
6. Verify whether items become unavailable to other users
```

### File Upload Quota Bypass

```
1. Identify the stated upload limit
2. Upload individual files within the limit — confirm it holds
3. Send CONCURRENT upload requests instead of sequential ones
4. Bypass any client-side-only size/count validation
5. Check total storage actually consumed server-side
```

**Impact:** Denial of service, revenue loss, resource exhaustion, storage cost abuse.

---

## 👤 Phase 10 — Account Enumeration & Subscription Logic

### Account Enumeration via Logic Flaws

```
1. Test login with a valid username + wrong password
2. Test login with an invalid username
3. Compare error messages AND response timing between the two
4. Repeat against the password-reset flow
5. Use timing differences to enumerate valid accounts at scale
```

### Subscription Downgrade Without Revocation

```
1. Subscribe to the premium tier, confirm premium feature access
2. Downgrade to the free tier
3. Re-check whether premium features are still accessible
4. Verify whether permissions/feature flags were actually revoked
   server-side, not just hidden in the UI
```

**Impact:** Information disclosure enabling targeted attacks, unauthorized continued access to paid features.

---

## 🛠️ Testing Methodology & Tools

### Essential Tools

```
• Burp Suite (Proxy, Repeater, Intruder, Turbo Intruder)
• Browser DevTools (hidden field / client-side validation inspection)
• Postman / Insomnia
• Custom scripts (Python requests) for scripted abuse flows
```

### Best Practices

```
✅ Use multiple accounts to test horizontal access
   (your own low-priv account vs a target account)
✅ Test every multi-step flow end-to-end, not just the final step
✅ Intercept EVERY request — never trust what the UI shows you
✅ Re-test after state changes (refund, downgrade, cart edit, logout)
✅ Test concurrency, not just sequential requests
✅ Document PoCs with clear before/after state (balance, inventory,
   access level) — logic bugs are proven by state, not payloads
```

### Common Indicators to Watch For

```
🚩 Prices/quantities editable client-side with no server re-check
🚩 Discount still applied after cart contents changed
🚩 Identical concurrent requests all succeeding past a stated limit
🚩 Admin-like paths reachable by a low-privilege account
🚩 Refund/cancel endpoints accepting a replayed request
🚩 Downgraded/free accounts retaining premium access
```

---

## ⚔️ Summary Workflow

```
┌────────────────────────────────────────────────────────┐
│           BUSINESS LOGIC BUG HUNTING WORKFLOW           │
├────────────────────────────────────────────────────────┤
│                                                          │
│  1. 🔍 Map the Full Flow (Burp, every step)             │
│            ↓                                            │
│  2. 💰 Test Price & Calculation Manipulation            │
│            ↓                                            │
│  3. 🎟️ Test Discount / Coupon / Gift Card Abuse         │
│            ↓                                            │
│  4. 📊 Test Documented Limits & Thresholds              │
│            ↓                                            │
│  5. 🔀 Test Workflow & Step Bypass                      │
│            ↓                                            │
│  6. ⚡ Test Race Conditions on Critical Ops              │
│            ↓                                            │
│  7. 🧠 Test Parameter Tampering & Forced Browsing        │
│            ↓                                            │
│  8. 📦 Test Order & Refund Replay/Modification          │
│            ↓                                            │
│  9. 📥 Test Inventory & Resource Abuse                  │
│            ↓                                            │
│ 10. 👤 Test Account Enumeration & Subscription Logic     │
│            ↓                                            │
│ 11. 📝 Document Before/After State & Report             │
│                                                          │
└────────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
What kind of flow are you testing?
    ├── Checkout / Pricing → Test negative values, client-side price
    │                         fields, integer overflow, formula injection
    │
    ├── Discounts / Coupons / Gift Cards → Test stacking, splitting,
    │                                       reuse, concurrent redemption
    │
    ├── Multi-step process (signup/2FA/checkout) → Try jumping straight
    │                                                to the final-step URL
    │
    ├── Balance-affecting action (withdraw/redeem) → Fire concurrent
    │                                                  requests (race condition)
    │
    ├── Role/permission visible in a request → Tamper the value,
    │                                            replay against a restricted route
    │
    ├── Refund / order-modify endpoint exists → Replay it / hit it
    │                                             post-approval
    │
    ├── Upload / cart-reservation feature → Test concurrency and
    │                                         abandonment behavior
    │
    └── Login / reset flow → Compare responses for valid vs invalid
                               accounts (enumeration)
```

---

<div align="center">

### 🔥 Map the flow. Break the assumption. Own the logic.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
