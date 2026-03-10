# API BUSINESS LOGIC FLAWS
---

## 1️⃣ API RATE LIMIT BYPASS
**How it works:** Rate limiting is implemented inconsistently across API endpoints, or limits are enforced per endpoint rather than per user/function.

**Steps to Find:**
1. Identify rate-limited endpoints (login, password reset, OTP)
2. Test different HTTP methods (POST vs GET vs PUT)
3. Vary headers (X-Forwarded-For, User-Agent)
4. Rotate API keys or session tokens
5. Use multiple IPs or proxy rotation
6. Check if limits reset per endpoint vs globally

**Impact:** Account enumeration, credential stuffing, DoS, data scraping

---

## 2️⃣ MASS ASSIGNMENT / OBJECT PROPERTY INJECTION
**How it works:** API accepts user input that directly modifies object properties without proper filtering, especially common in REST APIs using JSON/XML.

**Steps to Find:**
1. Inspect API documentation/Swagger for object schemas
2. Capture legitimate API requests
3. Add unexpected properties (isAdmin: true, role: "admin")
4. Modify read-only fields (balance: 999999, userId: 123)
5. Test nested object property injection
6. Check response for property changes

**Impact:** Privilege escalation, data corruption, unauthorized access

---

## 3️⃣ BATCH OPERATION ABUSE
**How it works:** APIs allow batch operations without proper validation of individual request limits or authorization checks.

**Steps to Find:**
1. Look for batch endpoints (/api/batch, /api/bulk)
2. Test if individual authorization checks are skipped
3. Mix high-privilege and low-privilege operations
4. Exceed reasonable batch size limits
5. Use batch to bypass rate limits
6. Check if atomicity is enforced (all-or-none)

**Impact:** Privilege escalation, data exfiltration, DoS

---

## 4️⃣ GRAPHQL BUSINESS LOGIC EXPLOITATION
**How it works:** GraphQL introspection reveals business logic fields, and complex queries bypass traditional security controls.

**Steps to Find:**
1. Enable GraphQL introspection (query { __schema })
2. Map all available queries and mutations
3. Test field/query depth limits (circular references)
4. Abuse query batching to bypass limits
5. Test directive manipulations (@include, @skip)
6. Probe for unpublished/undocumented mutations

**Impact:** Information disclosure, DoS via complex queries, unauthorized data access

---

## 5️⃣ IDOR VIA API PARAMETER MANIPULATION
**How it works:** Object references in API requests (IDs, UUIDs) are predictable or enumerable without proper authorization checks.

**Steps to Find:**
1. Identify object references in API paths (/api/users/{id})
2. Test sequential IDs (1001, 1002, 1003)
3. Test UUID patterns
4. Check different HTTP methods on same endpoint
5. Test with other users' tokens/sessions
6. Look for indirect object references

**Impact:** Data breach, unauthorized CRUD operations, PII exposure

---

## 6️⃣ API WEBHOOK MANIPULATION
**How it works:** Webhook endpoints accept user-controlled URLs or fail to validate webhook source/destination.

**Steps to Find:**
1. Find webhook configuration endpoints
2. Test SSRF via webhook URLs (http://internal-server)
3. Test open redirects in callback URLs
4. Spoof webhook signatures
5. Replay captured webhooks
6. Test race conditions in webhook processing

**Impact:** SSRF, data exfiltration, internal network access, replay attacks

---

## 7️⃣ API VERSIONING LOGIC FLAWS
**How it works:** Different API versions have inconsistent security controls, allowing attackers to use older/vulnerable versions.

**Steps to Find:**
1. Enumerate API versions (/v1/, /v2/, /beta/, /latest/)
2. Test same endpoints across different versions
3. Check if deprecated versions are still accessible
4. Compare authentication/authorization differences
5. Test version downgrade attacks
6. Look for version-specific bypasses

**Impact:** Bypass of security controls, access to deprecated features, inconsistent state

---

## 8️⃣ API CACHING LOGIC VULNERABILITIES
**How it works:** Sensitive data cached improperly, or cache keys don't account for user context/authorization.

**Steps to Find:**
1. Test cache headers in API responses
2. Check if authenticated data appears in unauthenticated cache
3. Test cache poisoning via parameter pollution
4. Verify cache keys include user context
5. Test time-based cache attacks
6. Check for cached error messages with sensitive data

**Impact:** Information disclosure, cache poisoning, unauthorized data access

---

## 9️⃣ API PAGINATION EXPLOITATION
**How it works:** Pagination parameters allow access to beyond intended data sets or bypass filtering.

**Steps to Find:**
1. Find pagination parameters (offset, limit, page, cursor)
2. Test extremely high limit values
3. Test negative offset values
4. Bypass filters via pagination
5. Access other users' data via offset manipulation
6. Check if sorting parameters affect authorization

**Impact:** Data exfiltration, bypass of access controls, resource exhaustion

---

## 🔟 API SUBSCRIPTION/TIER BYPASS
**How it works:** API usage limits or feature flags based on subscription tier are enforced client-side or inconsistently.

**Steps to Find:**
1. Identify tier/plan indicators in API responses
2. Test premium endpoints with free-tier tokens
3. Modify tier flags in requests/responses
4. Check rate limits per tier
5. Test if downgrade immediately affects API access
6. Probe for hidden premium features

**Impact:** Revenue loss, unauthorized feature access, resource abuse

---

## 1️⃣1️⃣ API AGGREGATION/ORCHESTRATION FLAWS
**How it works:** API gateways or aggregators don't properly propagate authentication/authorization to backend services.

**Steps to Find:**
1. Map API gateway vs backend service calls
2. Test if auth tokens are validated at each service
3. Check for direct backend service access
4. Test parameter passing between services
5. Identify trust boundaries
6. Test for confused deputy problems

**Impact:** Authorization bypass, direct backend access, privilege escalation

---

## 1️⃣2️⃣ API DEPENDENCY CHAIN EXPLOITATION
**How it works:** APIs that call other APIs don't properly handle errors or validate responses from dependencies.

**Steps to Find:**
1. Map API dependency chains
2. Simulate dependency failures/timeouts
3. Test with malformed dependency responses
4. Check error handling in chained calls
5. Test race conditions in dependency calls
6. Probe for circuit breaker bypasses

**Impact:** Business logic bypass, inconsistent state, data corruption

---

## 1️⃣3️⃣ API SEARCH/FILTER INJECTION
**How it works:** Search and filter parameters allow unauthorized data access or bypass business logic constraints.

**Steps to Find:**
1. Identify search/filter endpoints
2. Test complex filter operators (AND, OR, NOT)
3. Attempt SQL/NoSQL injection via filter parameters
4. Bypass filters to access restricted data
5. Test regex injection in search
6. Abuse filter chaining

**Impact:** Data leakage, unauthorized search, filter bypass

---

## 1️⃣4️⃣ API EVENT/STREAM MANIPULATION
**How it works:** Event-driven APIs (WebSockets, Server-Sent Events) don't validate event sequencing or origin.

**Steps to Find:**
1. Identify real-time/event endpoints
2. Test event replay
3. Manipulate event sequencing
4. Inject malicious events
5. Test event subscription authorization
6. Check for race conditions in event processing

**Impact:** Business logic manipulation, state corruption, unauthorized actions

---

## 1️⃣5️⃣ API KEY ROTATION/REVOCATION FLAWS
**How it works:** API key management lacks proper revocation checks or allows key reuse after revocation.

**Steps to Find:**
1. Test revoked API keys for continued access
2. Check key rotation mechanisms
3. Test if old keys work after rotation
4. Verify scope changes on key regeneration
5. Test key sharing between users
6. Check for key leakage in logs/errors

**Impact:** Unauthorized API access, privilege escalation, key abuse

---

## 1️⃣6️⃣ API RESOURCE EXHAUSTION
**How it works:** APIs allow creation of unlimited resources without proper quota enforcement or cleanup.

**Steps to Find:**
1. Identify resource creation endpoints
2. Test maximum resource limits
3. Create excessive resources (users, files, sessions)
4. Check for orphaned resource cleanup
5. Test recursive resource creation
6. Verify quotas are server-side enforced

**Impact:** DoS, storage exhaustion, performance degradation

---

## 1️⃣7️⃣ API STATE MACHINE BYPASS
**How it works:** Stateful APIs don't validate state transitions properly, allowing illegal operations.

**Steps to Find:**
1. Map API state machine (order: pending→paid→shipped)
2. Test skipping states (pending→shipped)
3. Test reversing states (shipped→pending)
4. Perform actions in wrong states
5. Check state validation consistency
6. Test concurrent state modifications

**Impact:** Business logic bypass, fraud, inconsistent state

---

## 1️⃣8️⃣ API METERING/BILLING BYPASS
**How it works:** API usage metering for billing purposes can be manipulated or bypassed.

**Steps to Find:**
1. Identify metered endpoints
2. Test if certain operations aren't metered
3. Manipulate request sizes/parameters to affect metering
4. Check metering consistency across API versions
5. Test metering aggregation flaws
6. Verify client-side vs server-side metering

**Impact:** Financial loss, service abuse, incorrect billing

---

## 1️⃣9️⃣ API SCHEMA VALIDATION BYPASS
**How it works:** API schema validation (OpenAPI/Swagger) can be bypassed through format confusion or validation gaps.

**Steps to Find:**
1. Obtain API schema/documentation
2. Test edge cases in data formats
3. Bypass required field validation
4. Test type confusion (string vs number)
5. Check for unvalidated additionalProperties
6. Test schema evolution issues

**Impact:** Injection attacks, data corruption, validation bypass

---

## 2️⃣0️⃣ API FEDERATION/DELEGATION FLAWS
**How it works:** APIs that delegate to third-party services don't properly validate delegation tokens or scopes.

**Steps to Find:**
1. Identify OAuth/OIDC delegation endpoints
2. Test scope escalation in delegation tokens
3. Reuse delegation tokens across contexts
4. Test token exchange flaws
5. Check for improper audience validation
6. Test cross-service privilege leakage

**Impact:** Unauthorized third-party access, privilege escalation, token theft

---

## 🔧 TESTING METHODOLOGY FOR API LOGIC FLAWS

### Preparation:
1. **API Documentation Review:** Swagger/OpenAPI, GraphQL schema
2. **Endpoint Discovery:** Directory brute forcing, parameter fuzzing
3. **Authentication Mapping:** API keys, JWT, OAuth flows

### Testing Approach:
1. **Business Flow Analysis:** Understand intended user journeys
2. **State Tracking:** Monitor how API maintains state
3. **Parameter Analysis:** Identify business logic parameters
4. **Error Message Analysis:** Extract logic clues from errors

### Tools:
- **Burp Suite:** API scanning, repeater, intruder
- **Postman:** API exploration, collection running
- **OWASP ZAP:** Automated API testing
- **Custom Scripts:** For race conditions, batch attacks
- **GraphQL IDEs:** Altair, GraphiQL for introspection

### Common Indicators:
- Inconsistent responses for similar operations
- Client-side enforcement of business rules
- Lack of server-side state validation
- Predictable resource identifiers
- Missing audit logs for critical operations
