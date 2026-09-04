# 🏴 Subdomain Takeover Methodology

> **A complete, structured approach to finding and verifying subdomain takeovers — from DNS recon to PoC.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-Subdomain%20Takeover-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-DNS%20%7C%20CNAME%20%7C%20Cloud%20Services-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-CLI%20%2B%20Manual%20Verification-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [What Is a Subdomain Takeover](#-what-is-a-subdomain-takeover)
2. [Phase 1 — Gather Subdomains & DNS Records](#-phase-1--gather-subdomains--dns-records)
3. [Phase 2 — Identify Dangling CNAMEs](#-phase-2--identify-dangling-cnames)
4. [Phase 3 — Automated Fingerprint Scanning](#-phase-3--automated-fingerprint-scanning)
5. [Phase 4 — Service-Specific Fingerprints (Manual Reference)](#-phase-4--service-specific-fingerprints-manual-reference)
6. [Phase 5 — Manual Verification](#-phase-5--manual-verification)
7. [Phase 6 — Claiming the Resource (Non-Destructive PoC)](#-phase-6--claiming-the-resource-non-destructive-poc)
8. [Phase 7 — Beyond CNAME: Other Takeover Vectors](#-phase-7--beyond-cname-other-takeover-vectors)
9. [Phase 8 — Continuous Monitoring](#-phase-8--continuous-monitoring)
10. [Summary Workflow](#️-summary-workflow)
11. [Quick Decision Tree](#-quick-decision-tree)

---

## 📖 What Is a Subdomain Takeover

```
1. A subdomain (sub.target.com) has a DNS record — usually a CNAME —
   pointing to an external service (S3 bucket, GitHub Pages, Heroku,
   Azure, Fastly, etc.)
2. That resource on the external service is deleted, expired, or was
   never claimed, but the DNS record still points at it
3. Since the service allocates resources by name (bucket name, app
   name, etc.) on a first-come-first-served basis, an attacker can
   register/create that exact resource on the third-party service
4. The moment they do, target.com's subdomain starts serving the
   attacker's content — full content control, cookie theft via shared
   parent-domain cookies, phishing, OAuth/CSP bypass, and more
```

> 💡 **Root cause in one line:** DNS points somewhere that no longer belongs to the target, and the "somewhere" is claimable by anyone.

---

## 🔍 Phase 1 — Gather Subdomains & DNS Records

Reuse your subdomain list from `recon.md` (`live_subs.txt` / `all_subs.txt`), then pull full DNS records for each.

```bash
# If you don't already have a subdomain list, generate one first
subfinder -d target.com -silent -all -recursive -o all_subs.txt

# Resolve every subdomain and grab CNAME + A records specifically
dnsx -l all_subs.txt -silent -cname -a -resp -o dns_records.txt

# Isolate only the ones that HAVE a CNAME (the takeover attack surface)
dnsx -l all_subs.txt -silent -cname -resp-only | sort -u > cname_records.txt
```

---

## 🧩 Phase 2 — Identify Dangling CNAMEs

A CNAME is "dangling" when it points to a hostname that doesn't resolve, or resolves but the underlying service returns a "not found / no such bucket / no app" style error.

```bash
# Step 1: Get subdomain → CNAME target pairs
dnsx -l all_subs.txt -silent -cname -resp -o cname_pairs.txt
# Format: sub.target.com [cname.target-service.com]

# Step 2: Check if the CNAME target itself resolves via NS lookup
cat cname_pairs.txt | awk -F'[][]' '{print $2}' | sort -u > cname_targets.txt

while read -r target; do
  result=$(dig +short "$target")
  if [[ -z "$result" ]]; then
    echo "[DANGLING - NXDOMAIN] $target"
  fi
done < cname_targets.txt

# Step 3: For CNAMEs that DO resolve, still check the HTTP response —
# many services (S3, Heroku, GH Pages) return an active IP but the
# CONTENT says "bucket does not exist" / "no such app"
httpx -l all_subs.txt -silent -mc 200,301,302,404,403 -title -sc -o cname_http_status.txt
```

---

## ⚙️ Phase 3 — Automated Fingerprint Scanning

🛠️ Tools: [Nuclei](https://github.com/projectdiscovery/nuclei) (recommended, actively maintained fingerprint templates), [Subjack](https://github.com/haccer/subjack), [Subzy](https://github.com/LukaSikic/subzy), [can-i-take-over-xyz](https://github.com/EdOverflow/can-i-take-over-xyz) (fingerprint reference database)

```bash
# Nuclei — most reliable, actively updated takeover-fingerprint templates
nuclei -l all_subs.txt -t http/takeovers/ -silent -o nuclei_takeovers.txt

# Subzy — purpose-built subdomain takeover checker
subzy run --targets all_subs.txt --hide_fails --verify_ssl -o subzy_results.txt

# Subjack — older but still useful as a second-opinion scanner,
# uses the fingerprints.json database
subjack -w all_subs.txt -t 100 -timeout 30 -o subjack_results.txt -ssl \
  -c ~/go/pkg/mod/github.com/haccer/subjack*/fingerprints.json
```

> Run at least two tools and cross-check results — false positives are common (a service returning a generic 404 that LOOKS like a takeover signature but isn't actually claimable).

---

## 🗂️ Phase 4 — Service-Specific Fingerprints (Manual Reference)

Use this table to manually confirm what an automated hit is telling you, and to know which platform's claim flow to follow.

| Service | CNAME Pattern | Vulnerable Response Signature |
|---|---|---|
| **AWS S3** | `*.s3.amazonaws.com`, `*.s3-website-*.amazonaws.com` | `NoSuchBucket` XML error |
| **GitHub Pages** | `*.github.io` | `There isn't a GitHub Pages site here.` |
| **Heroku** | `*.herokuapp.com` | `No such app` |
| **Fastly** | `*.fastly.net` | `Fastly error: unknown domain` |
| **Shopify** | `*.myshopify.com` | `Sorry, this shop is currently unavailable.` |
| **Azure (Cloud App)** | `*.azurewebsites.net` | `404 Web Site not found` |
| **Azure (Blob/CDN)** | `*.blob.core.windows.net`, `*.azureedge.net` | `The specified resource does not exist` |
| **Zendesk** | `*.zendesk.com` | `Help Center Closed` |
| **Unbounce** | `*.unbouncepages.com` | `The requested URL was not found on this server.` |
| **Tumblr** | `domain.tumblr.com` | `Whatever you were looking for doesn't currently exist at this address.` |
| **WordPress.com** | `*.wordpress.com` | `Do you want to register *.wordpress.com?` |
| **Cargo Collective** | `*.cargocollective.com` | `404 Not Found` |
| **Surge.sh** | `*.surge.sh` | `project not found` |
| **Bitbucket** | `*.bitbucket.io` | `Repository not found` |
| **Netlify** | `*.netlify.app` | `Not Found - Request ID:` |
| **Vercel** | `*.vercel.app` | `404: NOT_FOUND` |
| **Readme.io** | `*.readme.io` | `Project doesnt exist... yet!` |
| **UserVoice** | `*.uservoice.com` | `This UserVoice subdomain is currently available!` |
| **Ghost** | `*.ghost.io` | `The thing you were looking for is no longer here` |
| **Pantheon** | `*.pantheonsite.io` | `The gods are wise, but do not know of the site which you seek.` |
| **Cargo/Campaign Monitor** | `*.createsend.com` | `Double check the URL` |

> 📚 Full, community-maintained fingerprint database with claim instructions: [EdOverflow/can-i-take-over-xyz](https://github.com/EdOverflow/can-i-take-over-xyz)

---

## 🔬 Phase 5 — Manual Verification

Before attempting any PoC, confirm the finding is real and not a false positive.

```
1. Re-check the CNAME with dig/nslookup right before testing — DNS can
   change between the automated scan and now
     dig CNAME sub.target.com +short

2. curl the subdomain directly and read the FULL response body, not
   just the status code — some services return 200 OK with a "not
   found" message baked into the HTML
     curl -sI https://sub.target.com
     curl -s https://sub.target.com | head -50

3. Check whether the third-party resource name is actually claimable:
     - For S3: try `aws s3 ls s3://bucket-name` (anonymous) or check
       via the S3 console — is the bucket name available to register?
     - For GitHub Pages: is the org/repo referenced in the CNAME
       actually deleted / does the username exist?
     - For SaaS platforms (Shopify, Zendesk, etc.): does their signup
       flow let you register that exact subdomain/project name?

4. Rule out wildcard DNS — if *.target.com resolves to the same dangling
   target for literally any subdomain, it may be an intentional wildcard
   catch-all rather than a real dangling record. Test with a random
   nonsense subdomain: random123xyz.target.com
```

---

## 🎯 Phase 6 — Claiming the Resource (Non-Destructive PoC)

> ⚠️ **Scope & ethics check first.** Only proceed if subdomain takeover is explicitly in-scope for the program, and always follow the minimum-impact PoC principle — claim just enough to prove control, screenshot it, then release/report immediately per program rules. Never hosts content, phishing pages, or anything beyond a benign proof page.

```
1. Register the exact resource name referenced in the dangling CNAME
   on the third-party service (following that service's normal signup
   flow — e.g. create the S3 bucket with the exact bucket name, create
   the GitHub Pages repo with the exact name, create the Heroku app
   with the exact app name)
2. Upload a minimal, clearly-labeled proof file (e.g. a plain text/HTML
   page identifying it as an authorized security test with your
   handle/contact and the report reference)
3. Re-visit https://sub.target.com and confirm YOUR content now loads
4. Screenshot the working PoC (URL bar + content clearly visible)
5. Immediately report to the program — do not leave the claimed
   resource live/public longer than necessary to document the PoC
6. Release/delete the claimed resource once the report is filed and
   acknowledged, unless the program specifically asks you to keep it
   for their own verification
```

---

## 🧬 Phase 7 — Beyond CNAME: Other Takeover Vectors

Subdomain takeover isn't only about CNAME records — check these too:

```
1. MX record takeover — dangling MX pointing at an email service
   (e.g. an abandoned SendGrid/Mailgun domain) can let an attacker
   receive mail for that subdomain (password resets, verification
   codes, sensitive notifications)

2. NS record takeover — if a subdomain's NS records point to a
   name server that's no longer registered/claimed (e.g. an expired
   AWS Route53 hosted zone, or a deleted DigitalOcean/Cloudflare
   nameserver setup), the attacker can register that NS and control
   ALL DNS responses for that subdomain, not just one record

3. TXT record / SPF takeover — abandoned third-party TXT verification
   records can sometimes be re-claimed to spoof domain verification
   with that third party (e.g. re-verify ownership on a SaaS platform
   the org no longer uses, and pivot into their org's linked resources)

4. Azure/AWS resource-group orphaning — cloud resources referenced by
   name in DNS (storage accounts, CDN endpoints, traffic manager
   profiles) that were deleted from the cloud account but not from DNS
```

---

## 🔁 Phase 8 — Continuous Monitoring

Subdomain takeovers are often introduced AFTER initial recon — a service gets decommissioned weeks or months later and nobody cleans up the DNS record. Treat this as an ongoing check, not a one-time scan.

```bash
# Re-run subdomain enum + takeover scan on a schedule (cron) and diff
# against the previous run to catch newly-dangling CNAMEs

subfinder -d target.com -silent -all -recursive -o all_subs_new.txt
diff all_subs.txt all_subs_new.txt

nuclei -l all_subs_new.txt -t http/takeovers/ -silent -o nuclei_takeovers_new.txt

# Or wire it into notify for push alerts on new findings
subfinder -d target.com -silent | dnsx -silent -cname | \
  nuclei -t http/takeovers/ -silent | notify
```

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│           SUBDOMAIN TAKEOVER WORKFLOW                 │
├──────────────────────────────────────────────────────┤
│                                                        │
│  1. 🌐 Gather Subdomains & Full DNS Records           │
│            ↓                                          │
│  2. 🧩 Isolate CNAMEs → Check for Dangling Targets    │
│            ↓                                          │
│  3. ⚙️ Run Nuclei + Subzy + Subjack (cross-check)     │
│            ↓                                          │
│  4. 🗂️ Match Response Against Fingerprint Table       │
│            ↓                                          │
│  5. 🔬 Manually Verify (dig, curl, wildcard check)    │
│            ↓                                          │
│  6. 🎯 Claim Resource → Screenshot PoC → Report        │
│            ↓                                          │
│  7. 🧬 Check MX / NS / TXT Takeover Vectors Too       │
│            ↓                                          │
│  8. 🔁 Re-Scan Periodically for New Dangling Records  │
│            ↓                                          │
│  9. 📝 Document & Report                              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
Subdomain has a CNAME record?
    ├── NO → check MX/NS/TXT instead (Phase 7)
    │
    ├── YES → does the CNAME target resolve?
    │           ├── NO (NXDOMAIN) → likely dangling → verify (Phase 5)
    │           │
    │           └── YES → does the HTTP response match a known
    │                     "not claimed" fingerprint? (Phase 4 table)
    │                       ├── YES → verify it's not a wildcard catch-all
    │                       │         → confirm resource is claimable
    │                       │         → PoC (Phase 6)
    │                       └── NO  → likely a false positive, skip
    │
    └── Wildcard DNS on the domain? → sanity-check with a random
                                       nonsense subdomain before
                                       trusting any single result
```

---

### 📚 Resources

- 🔗 [EdOverflow — can-i-take-over-xyz (fingerprint DB)](https://github.com/EdOverflow/can-i-take-over-xyz)
- 🔗 [Nuclei Takeover Templates](https://github.com/projectdiscovery/nuclei-templates/tree/main/http/takeovers)
- 🔗 [Subzy](https://github.com/LukaSikic/subzy)
- 🔗 [Subjack](https://github.com/haccer/subjack)
- 🔗 [HackTricks — Domain/Subdomain Takeover](https://book.hacktricks.xyz/pentesting-web/domain-subdomain-takeover)
- Companion docs: `recon.md`, `API-Testing-Methodology.md`, `2FA-Bypass.md`

---

<div align="center">

### 🔥 Find the dangling record. Claim it clean. Report it fast.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
