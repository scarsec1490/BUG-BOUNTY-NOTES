BUSINESS LOGIC BUGS FOR WEB APPLICATIONS
==========================================

1️⃣ NEGATIVE PRICE MANIPULATION
How it works: Application accepts negative values for prices or quantities without server-side validation.

Steps to Find:
1. Identify price/quantity parameters in checkout flow
2. Use proxy tool (Burp Suite) to intercept requests
3. Modify price parameter to negative value (e.g., -999)
4. Modify quantity to negative integers
5. Submit the modified request
6. Check if transaction processes with negative amount

Impact: Financial loss, users receiving products plus money, inventory manipulation

---

2️⃣ DISCOUNT/COUPON STACKING ABUSE
How it works: Application fails to check if discount was already applied or if order changed after discount.

Steps to Find:
1. Add items to cart until discount threshold is met
2. Apply discount/coupon code
3. Remove items from cart after discount applied
4. Complete purchase with discount on reduced order
5. Try applying multiple expired coupons
6. Test concurrent coupon redemption requests

Impact: Revenue loss, discount abuse, financial fraud

---

3️⃣ INVESTMENT LIMIT OVERRIDE
How it works: Investment limits enforced only in UI, not on server-side.

Steps to Find:
1. Find investment/transaction limits in documentation
2. Try to exceed limit via UI (note the error)
3. Intercept the transaction request with proxy
4. Locate amount/limit parameters in request
5. Modify values to exceed documented limits
6. Check if transaction processes successfully

Impact: Risk management failure, regulatory exposure, financial losses

---

4️⃣ WORKFLOW STEP BYPASS
How it works: Multi-step processes don't verify completion of previous steps.

Steps to Find:
1. Identify multi-step workflows (checkout, registration, 2FA)
2. Complete first step and capture request
3. Jump directly to final step URL
4. Skip payment/verification steps entirely
5. Access confirmation pages directly
6. Check if workflow completes without authentication

Impact: Authentication bypass, payment bypass, privilege escalation

---

5️⃣ RACE CONDITION EXPLOITATION
How it works: Simultaneous requests bypass balance/inventory checks due to poor locking mechanisms.

Steps to Find:
1. Identify critical operations (withdrawals, redemptions)
2. Send single legitimate request first
3. Use Turbo Intruder or custom script
4. Send multiple concurrent identical requests
5. Check if all requests succeed despite constraints
6. Verify account balance or inventory depletion

Impact: Double spending, overdrafts, inventory overselling, unlimited redemptions

---

6️⃣ CLIENT-SIDE PRICE MANIPULATION
How it works: Prices stored in hidden fields or client-side parameters without server validation.

Steps to Find:
1. Inspect HTML source for hidden price fields
2. Use browser developer tools to modify values
3. Intercept POST request with proxy tool
4. Locate price parameter (e.g., price=100)
5. Change to arbitrary value (price=1)
6. Complete transaction with modified price

Impact: Revenue loss, fraud, inventory given away

---

7️⃣ PARAMETER TAMPERING
How it works: User role, permissions, or sensitive data passed in client-controllable parameters.

Steps to Find:
1. Capture requests with parameters like role=user
2. Identify privilege/permission indicators
3. Modify to elevated values (role=admin)
4. Change user IDs to access other accounts
5. Alter boolean flags (isAdmin=true)
6. Test access to restricted resources

Impact: Privilege escalation, unauthorized access, horizontal/vertical authorization bypass

---

8️⃣ REFUND/RETURN ABUSE
How it works: System fails to validate if order already refunded or returned.

Steps to Find:
1. Complete legitimate purchase
2. Request refund through normal flow
3. Capture and replay refund request
4. Check for duplicate refund validation
5. Try refunding already refunded orders
6. Test canceling shipped orders

Impact: Financial loss, inventory discrepancies, fraud

---

9️⃣ TWO-FACTOR AUTHENTICATION BYPASS
How it works: 2FA verification not enforced on subsequent requests after initial login.

Steps to Find:
1. Start login process with valid credentials
2. Reach 2FA verification page
3. Note the post-2FA destination URL
4. Skip 2FA by directly accessing destination
5. Check if session grants access
6. Test if 2FA token is validated

Impact: Complete authentication bypass, account takeover

---

🔟 INVENTORY RESERVATION WITHOUT PAYMENT
How it works: Items reserved in cart without purchase, preventing legitimate sales.

Steps to Find:
1. Add high-demand items to shopping cart
2. Abandon cart without completing purchase
3. Check if inventory remains reserved
4. Add maximum quantities and abandon
5. Test timeout mechanisms
6. Verify if items become unavailable to others

Impact: Denial of service, inventory manipulation, revenue loss

---

1️⃣1️⃣ INTEGER OVERFLOW/UNDERFLOW
How it works: Extremely high or low values cause calculation errors.

Steps to Find:
1. Identify numeric input fields (quantity, amount)
2. Test with maximum integer values
3. Try boundary values (2147483647 for 32-bit)
4. Use values that cause overflow to negative
5. Test decimal values where integers expected
6. Check calculation results for anomalies

Impact: Free products, incorrect charges, system crashes

---

1️⃣2️⃣ ORDER MODIFICATION AFTER APPROVAL
How it works: Orders can be modified after approval but before fulfillment.

Steps to Find:
1. Place and approve an order
2. Capture order confirmation request
3. Find order modification endpoints
4. Attempt to modify approved order details
5. Change quantities or items post-approval
6. Check if modifications are processed

Impact: Fraud, inventory issues, fulfillment errors

---

1️⃣3️⃣ SESSION FIXATION IN STATE TRANSITIONS
How it works: Session state not properly validated during workflow transitions.

Steps to Find:
1. Start workflow in one state/role
2. Obtain session token
3. Change context (account, role, permission)
4. Reuse old session token
5. Access resources from previous context
6. Check if authorization properly revalidated

Impact: Unauthorized access, privilege escalation, data exposure

---

1️⃣4️⃣ FORMULA INJECTION IN CALCULATIONS
How it works: User input incorporated into price calculations without sanitization.

Steps to Find:
1. Locate fields affecting price calculations
2. Input mathematical expressions (e.g., "1+1")
3. Try formulas that manipulate total
4. Test with division by zero
5. Inject negative multipliers
6. Verify if calculations process injection

Impact: Price manipulation, incorrect charges, system errors

---

1️⃣5️⃣ BULK DISCOUNT EXPLOITATION
How it works: Bulk discounts applied incorrectly or repeatedly.

Steps to Find:
1. Identify bulk discount thresholds
2. Add items to reach threshold
3. Apply discount to cart
4. Remove items below threshold
5. Try splitting orders to abuse discount
6. Test if discount persists after modification

Impact: Revenue loss, discount abuse

---

1️⃣6️⃣ ACCOUNT ENUMERATION VIA LOGIC FLAWS
How it works: Different responses reveal valid vs invalid accounts.

Steps to Find:
1. Test login with valid username, wrong password
2. Test with invalid username
3. Compare response times and error messages
4. Check password reset functionality
5. Note differences in responses
6. Use timing attacks to enumerate accounts

Impact: Information disclosure, targeted attacks, account takeover preparation

---

1️⃣7️⃣ GIFT CARD/CREDIT ABUSE
How it works: Gift cards or credits applied multiple times or beyond limits.

Steps to Find:
1. Obtain valid gift card code
2. Apply to one purchase
3. Try applying same code to multiple orders
4. Test partial redemptions
5. Check if balance tracking is accurate
6. Try negative balance scenarios

Impact: Financial fraud, revenue loss

---

1️⃣8️⃣ SUBSCRIPTION DOWNGRADE TO FREE
How it works: Paid subscription can be downgraded but features remain accessible.

Steps to Find:
1. Subscribe to premium tier
2. Access premium features
3. Downgrade to free tier
4. Check if premium features still accessible
5. Test if permissions properly revoked
6. Verify feature flags updated

Impact: Revenue loss, unauthorized feature access

---

1️⃣9️⃣ FILE UPLOAD QUOTA BYPASS
How it works: Upload limits enforced only client-side or per-request basis.

Steps to Find:
1. Identify file upload limits
2. Upload files within limit individually
3. Send concurrent upload requests
4. Bypass client-side validation
5. Check total storage consumed
6. Test if server-side limits enforced

Impact: Resource exhaustion, storage costs, denial of service

---

2️⃣0️⃣ FORCED BROWSING TO ADMIN FUNCTIONS
How it works: Administrative endpoints accessible without proper authorization checks.

Steps to Find:
1. Map application endpoints and URLs
2. Identify admin-like paths (/admin, /dashboard)
3. Access directly with low-privilege account
4. Test HTTP methods (GET, POST, PUT, DELETE)
5. Check for directory listings
6. Verify if authorization enforced

Impact: Full system compromise, unauthorized admin access, data breach

---
