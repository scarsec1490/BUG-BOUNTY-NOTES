# 🕵️ Recon Methodology

> **A complete, structured recon workflow — from subdomains to juicy endpoints — for bug hunting.**

---

<div align="center">

![Type](https://img.shields.io/badge/Phase-Reconnaissance-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-Subdomains%20%7C%20IPs%20%7C%20URLs%20%7C%20Endpoints-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-CLI%20%2B%20Automation-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Phase 1 — Subdomain Enumeration](#-phase-1--subdomain-enumeration)
2. [Phase 2 — IP Address Enumeration](#-phase-2--ip-address-enumeration)
3. [Phase 3 — Crawling & URL Collection](#-phase-3--crawling--url-collection)
4. [Phase 4 — URL Filtering & Categorization](#-phase-4--url-filtering--categorization)
5. [Phase 5 — Juicy Endpoint & Subdomain Hunting](#-phase-5--juicy-endpoint--subdomain-hunting)
6. [Summary Workflow](#️-summary-workflow)
7. [Quick Decision Tree](#-quick-decision-tree)

---

## 🌐 Phase 1 — Subdomain Enumeration

### 1.1 — Passive Subdomain Enumeration

🛠️ Tools: [Subfinder](https://github.com/projectdiscovery/subfinder), [Amass](https://github.com/OWASP/Amass), [crt.sh](https://crt.sh/), [Assetfinder](https://github.com/tomnomnom/assetfinder), [Github-Subdomains](https://github.com/gwen001/github-subdomains), [Chaos](https://chaos.projectdiscovery.io/)

```bash
# Subfinder
subfinder -d target.com -silent -all -recursive -o subfinder_subs.txt

# Amass (passive mode)
amass enum -passive -d target.com -o amass_passive_subs.txt

# Assetfinder
assetfinder --subs-only target.com | anew assetfinder_subs.txt

# crt.sh (certificate transparency, via curl + jq)
curl -s "https://crt.sh/?q=%25.target.com&output=json" | jq -r '.[].name_value' | \
  sed 's/\*\.//g' | sort -u | anew crtsh_subs.txt

# Github subdomains (needs a GitHub token)
github-subdomains -d target.com -t $GITHUB_TOKEN -o github_subs.txt

# Chaos dataset (ProjectDiscovery)
chaos -d target.com -silent -o chaos_subs.txt
```

### 1.2 — Active / Brute-Force Subdomain Enumeration

🛠️ Tools: [Puredns](https://github.com/d3mondev/puredns), [Amass (active)](https://github.com/OWASP/Amass), [ShuffleDNS](https://github.com/projectdiscovery/shuffledns)

```bash
# Puredns with a resolver list + wordlist (fast, low false positives)
puredns bruteforce /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt \
  target.com -r resolvers.txt -w puredns_subs.txt

# Amass active enum (brute + recursive + intel)
amass enum -active -d target.com -brute -w subdomains-top1million.txt -o amass_active_subs.txt

# ShuffleDNS
shuffledns -d target.com -w wordlist.txt -r resolvers.txt -o shuffledns_subs.txt
```

### 1.3 — Permutation Scanning (find subs like dev-api, api-stage, etc.)

🛠️ Tools: [Gotator](https://github.com/Josue87/gotator), [AlterX](https://github.com/projectdiscovery/alterx)

```bash
# Generate permutations from known subs, then resolve
gotator -sub subfinder_subs.txt -perm permutations_wordlist.txt -depth 1 -numbers 3 -mindup -adv -md > gotator_perms.txt
puredns resolve gotator_perms.txt -r resolvers.txt -w permutation_subs.txt

# AlterX (pattern-based permutation)
cat subfinder_subs.txt | alterx -silent | puredns resolve -r resolvers.txt -w alterx_subs.txt
```

### 1.4 — Merge, Dedup & Resolve

```bash
cat *_subs.txt | sort -u | anew all_subs.txt

# Resolve to confirm which subdomains actually exist (kill dead DNS entries)
puredns resolve all_subs.txt -r resolvers.txt -w resolved_subs.txt
```

### 1.5 — Subdomain Probing (alive hosts + fingerprinting)

🛠️ Tools: [httpx](https://github.com/projectdiscovery/httpx)

```bash
httpx -l resolved_subs.txt -p 80,443,8080,8443,8000,8888,9000,3000 \
  -silent -title -sc -ip -cl -td -tech-detect -o live_subs.txt
```

> `live_subs.txt` is your master list of alive, in-scope hosts — everything downstream (IP enum, crawling, fuzzing) branches off this.

---

## 🖧 Phase 2 — IP Address Enumeration

> ⚠️ **Note:** ASN/CIDR-based IP hunting is only meaningful for **large targets** that own their own network blocks (Google, Apple, Meta, large enterprises, etc.). Small targets sitting entirely behind shared cloud infra (Cloudflare, AWS shared IPs, etc.) usually have no ASN of their own — for those, stick to the `live_subs.txt` IPs from httpx above.

### My IP Enumeration Methodology

```
STEP 1: Find the ASN number(s) of the target
STEP 2: Find CIDRs / IP ranges owned by that ASN
STEP 3: Expand CIDRs into individual IPs and merge
STEP 4: Find which of those IPs are alive
STEP 5: Split results into an IP list and a subdomain list (via rDNS)
STEP 6: Scan alive IPs for open ports
STEP 7: Run service/version detection on open ports
```

### 2.1 — Find the ASN Number

🛠️ Sources: [bgp.he.net](https://bgp.he.net/), [whois.arin.net](https://whois.arin.net/ui/)

```bash
# Quick CLI lookup via whois
whois -h whois.radb.net -- '-i origin AS-TARGETNAME' | grep -Eo '([0-9.]+){4}/[0-9]+' 

# Or just search the org name on bgp.he.net / whois.arin.net manually
# to get the ASxxxxx number(s) associated with the target
```

### 2.2 — Find CIDRs Inside That ASN

🛠️ Tool (preferred): [asnmap](https://github.com/projectdiscovery/asnmap) | Web: [mxtoolbox](https://mxtoolbox.com/SuperTool.aspx)

```bash
# From ASN number
asnmap -a AS15169 -silent -o cidrs.txt

# From org/domain directly (asnmap can resolve org → ASN → CIDR in one go)
asnmap -d target.com -silent -o cidrs.txt
```

### 2.3 — Expand CIDRs into IP Addresses

🛠️ Tool (preferred): [mapcidr](https://github.com/projectdiscovery/mapcidr) | Web: [ipaddressguide.com/cidr](https://www.ipaddressguide.com/cidr)

```bash
# Expand every CIDR in the file into individual IPs
mapcidr -cl cidrs.txt -silent -o all_ips.txt

# Useful extras: aggregate overlapping CIDRs first, then expand
mapcidr -cl cidrs.txt -aggregate -silent -o cidrs_aggregated.txt
mapcidr -cl cidrs_aggregated.txt -silent -o all_ips.txt
```

### 2.4 — Find Alive IPs

🛠️ Tools (preferred): **Angry IP Scanner**, [Naabu](https://github.com/projectdiscovery/naabu), [Masscan](https://github.com/robertdavidgraham/masscan)

```bash
# Angry IP Scanner is GUI-based — point it at all_ips.txt / the CIDR range,
# enable ping + port check, export results as CSV/TXT

# CLI alternative — naabu as a fast alive-check (port 80/443 sweep)
naabu -l all_ips.txt -p 80,443 -silent -o alive_ips.txt

# Or masscan for very large ranges
masscan -iL all_ips.txt -p80,443 --rate 10000 -oL masscan_alive.txt
```

**Custom scanning script** (wraps the above scan/alive-check pipeline):
🔗 [ipscanner.sh — scarsec1490/Bug-Hunting-Scripts](https://github.com/scarsec1490/Bug-Hunting-Scripts/blob/main/ipscanner.sh)

```bash
git clone https://github.com/scarsec1490/Bug-Hunting-Scripts.git
cd Bug-Hunting-Scripts
chmod +x ipscanner.sh
./ipscanner.sh -l all_ips.txt   # check the script's own -h/--help for exact flags
```

### 2.5 — Reverse DNS: Find More Subdomains from Alive IPs

🛠️ Tools: [dnsx](https://github.com/projectdiscovery/dnsx), Angry IP Scanner (built-in rDNS)

```bash
# dnsx reverse lookup on the alive IP list
dnsx -l alive_ips.txt -ptr -resp-only -silent -o rdns_subs.txt

# Angry IP Scanner also does rDNS while scanning — export the "Hostname"
# column and filter it into its own list with a quick script:
awk -F',' '{print $2}' angryip_export.csv | grep -v '^$' | sort -u > rdns_subs_angryip.txt
```

Merge any new subdomains found here back into `all_subs.txt` and re-run Phase 1.5 (httpx probing) on the new entries.

### 2.6 — Port Scanning on Alive IPs

🛠️ Tools (preferred): [Naabu](https://github.com/projectdiscovery/naabu), [Masscan](https://github.com/robertdavidgraham/masscan)

> Full nmap sweeps across thousands of IPs are too slow — use naabu/masscan for the initial full-port sweep, THEN run nmap only on the ports that came back open.

```bash
# Naabu full port sweep
naabu -l alive_ips.txt -p - -silent -o open_ports.txt

# Masscan full port sweep (faster on very large ranges)
masscan -iL alive_ips.txt -p1-65535 --rate 20000 -oL masscan_ports.txt
```

### 2.7 — Service & Version Detection

🛠️ Tool: [nmap](https://nmap.org/)

```bash
# Feed naabu's IP:port output into nmap for targeted service/version detection
naabu -l alive_ips.txt -p - -silent | nmap -sV -sC -iL - -oA nmap_services
```

---

## 🕸️ Phase 3 — Crawling & URL Collection

🛠️ Tools: [Katana](https://github.com/projectdiscovery/katana), [gau](https://github.com/lc/gau), [waybackurls](https://github.com/tomnomnom/waybackurls), [gauplus](https://github.com/bp0lr/gauplus), [urlfinder](https://github.com/projectdiscovery/urlfinder), Google dorking, JS crawling

### 3.1 — Active Crawling

```bash
# Katana — active crawl, capture JS-parsed endpoints too
katana -u live_subs.txt -silent -jc -kf all -d 5 -o katana_results.txt

# Katana with form filling + headless mode for JS-heavy apps
katana -u live_subs.txt -silent -jc -headless -kf all -d 5 -o katana_headless.txt
```

### 3.2 — Passive URL Collection

```bash
# GAU (fetches from Wayback, Common Crawl, OTX, URLScan)
cat live_subs.txt | awk '{print $1}' | gau --subs --threads 10 | anew gau_results.txt

# Waybackurls
cat live_subs.txt | awk '{print $1}' | waybackurls | anew wayback_results.txt

# gauplus (alternate GAU implementation, sometimes catches more)
echo target.com | gauplus -subs -t 10 | anew gauplus_results.txt

# urlfinder (ProjectDiscovery, aggregates multiple passive sources)
urlfinder -d target.com -silent -o urlfinder_results.txt
```

### 3.3 — Other URL Sources Worth Checking

```
- Common Crawl index:      https://index.commoncrawl.org/
- URLScan.io search:       https://urlscan.io/search/#target.com
- Google dorks:            site:target.com inurl:api | inurl:v1 | inurl:v2
- GitHub/GitLab dorking:   search org repos for hardcoded endpoint strings
- Postman public workspaces / API collections leaked publicly
- Mobile app APKs (apktool/jadx) — often hardcode full API base URLs
```

### 3.4 — Merge Everything into allurls.txt

```bash
cat katana_results.txt katana_headless.txt gau_results.txt wayback_results.txt \
    gauplus_results.txt urlfinder_results.txt | sort -u | anew allurls.txt
```

`allurls.txt` is now your master URL corpus — everything in Phase 4 and 5 filters down from this single file.

---

## 🗂️ Phase 4 — URL Filtering & Categorization

Raw `allurls.txt` is huge and noisy. Split it into purpose-built files before hunting.

### 4.1 — Clean & Deduplicate Similar URLs

🛠️ Tool: [uro](https://github.com/s0md3v/uro)

```bash
# uro strips near-duplicate URLs (same path, different param values, etc.)
cat allurls.txt | uro -o allurls_deduped.txt
```

### 4.2 — Split Into Purpose-Built Lists

```bash
# All URLs that carry parameters
grep -E '\?[a-zA-Z0-9_]+=' allurls_deduped.txt | sort -u > params.txt

# All JS files (mine these separately for hardcoded endpoints/secrets)
grep -Ei '\.js(\?|$)' allurls_deduped.txt | sort -u > jsfiles.txt

# All endpoints with no params (good for directory/BOLA/method-tamper testing)
grep -Ev '\?' allurls_deduped.txt | sort -u > clean_endpoints.txt
```

### 4.3 — Vulnerability-Class Sorting with gf

🛠️ Tools: [gf](https://github.com/tomnomnom/gf) + [Gf-Patterns](https://github.com/1ndianl33t/Gf-Patterns)

```bash
cat params.txt | gf sqli   | anew sqli_params.txt
cat params.txt | gf xss    | anew xss_params.txt
cat params.txt | gf ssrf   | anew ssrf_params.txt
cat params.txt | gf lfi    | anew lfi_params.txt
cat params.txt | gf rce    | anew rce_params.txt
cat params.txt | gf redirect | anew redirect_params.txt
cat params.txt | gf idor   | anew idor_params.txt
```

**Custom automation script** (wraps uro + gf + category sorting in one pass):
🔗 [paramgrep.sh — scarsec1490/Bug-Hunting-Scripts](https://github.com/scarsec1490/Bug-Hunting-Scripts/blob/main/paramgrep.sh)

```bash
git clone https://github.com/scarsec1490/Bug-Hunting-Scripts.git
cd Bug-Hunting-Scripts
chmod +x paramgrep.sh
./paramgrep.sh -f allurls_deduped.txt -o output_dir/   # check script's -h for exact flags
```

---

## 💎 Phase 5 — Juicy Endpoint & Subdomain Hunting

Now hunt through `live_subs.txt` and `allurls.txt` for high-value targets.

### 5.1 — Interesting Files (backups, configs, keys, DB dumps)

```bash
cat allurls.txt | grep -E "\.(xls|xml|xlsx|json|pdf|sql|doc|docx|pptx|txt|zip|tar\.gz|tgz|bak|7z|rar|log|cache|secret|db|backup|yml|gz|config|csv|yaml|md|md5|tar|xz|7zip|p12|pem|key|crt|csr|sh|pl|py|java|class|jar|war|ear|sqlitedb|sqlite3|dbf|db3|accdb|mdb|sqlcipher|gitignore|env|ini|conf|properties|plist|cfg)$" | sort -u > interesting_files.txt
```

### 5.2 — Juicy Subdomains (from live_subs.txt)

```bash
cat live_subs.txt | grep -Ei "admin|administrator|panel|dashboard|manage|control|api|rest|graphql|v[0-9]+|dev|test|testing|stage|staging|qa|uat|preprod|sandbox|login|signin|signup|auth|sso|oauth|account|user|profile|session|token|jwt|verify|reset|password|otp|mfa|2fa|cdn|static|media|assets|files|storage|upload|download|bucket|s3|blob|old|backup|bak|legacy|archive|copy|clone|monitor|monitoring|status|health|metrics|alert|grafana|prometheus|kibana|elastic|logs|debug|trace|tmp|cache|error|dump|aws|gcp|azure|cloud|k8s|docker|jenkins|ci|cd|git|gitlab|github|bitbucket|service|gateway|proxy|edge|backend|billing|payment|invoice|order|cart|wallet|transaction|internal|private" | sort -u > juicy_subs.txt
```

### 5.3 — API-Specific Subdomains

```bash
cat live_subs.txt | grep -Ei '^(https?:\/\/)?(api|apis|api[0-9]*|rest|restapi|graphql|gql|gateway|gw|ws|wss|socket|rpc|grpc|soap|internal|int|dev-api|stage-api|staging-api|test-api|uat-api|sandbox|sb|admin-api|partner-api|public-api|private-api|mobile-api|m-api|app-api|apidocs|api-docs|docs-api|swagger|openapi|apigee|apim|apigateway|edge|backend|be|bff|micro|microservice|services?|svc|v[0-9]+-api|api-v[0-9]+)\.' | sort -u > api_subs_juicy.txt
```

### 5.4 — Auth-Related Endpoints (from allurls.txt)

```bash
cat allurls.txt | grep -EiP '/(login|signin|sign-in|signup|sign-up|register|auth|authenticate|authorize|oauth|oauth2|sso|saml|token|refresh[-_]?token|access[-_]?token|session|logout|reset[-_]?password|forgot[-_]?password|change[-_]?password|verify|verification|confirm|activate|otp|2fa|mfa|totp|passwordless|magic[-_]?link|callback|redirect_uri|client_id|client_secret|grant_type|jwt|id_token)\b' | sort -u > auth_endpoints.txt
```

Auth-related **subdomains** (from live_subs.txt) with the same intent:

```bash
cat live_subs.txt | grep -Ei "auth|login|signin|signup|sso|oauth|account|accounts|identity|idp|session|token|passport" | sort -u > auth_subs.txt
```

### 5.5 — IDOR-Prone Endpoints (from allurls.txt)

IDOR candidates are URLs that reference an object via a numeric ID, UUID, or an object-name parameter — these are exactly what you replay across accounts in Phase 3 of the API testing doc.

```bash
cat allurls.txt | grep -EiP '(\/(user|users|account|accounts|profile|profiles|member|members|customer|customers|client|clients|order|orders|invoice|invoices|payment|payments|transaction|transactions|ticket|tickets|booking|bookings|reservation|reservations|document|documents|doc|docs|file|files|report|reports|message|messages|chat|chats|conversation|conversations|note|notes|comment|comments|post|posts|task|tasks|project|projects|team|teams|org|orgs|organization|organizations|group|groups|cart|wallet|card|cards|address|addresses|contract|contracts|application|applications|submission|submissions|request|requests)\/[0-9]+\b)|(\/(user|users|account|accounts|profile|profiles|member|members|customer|customers|order|orders|invoice|invoices|payment|payments|transaction|transactions|ticket|tickets|booking|document|documents|file|files)\/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b)|([?&](id|user_id|userid|uid|account_id|acct_id|profile_id|member_id|customer_id|client_id|order_id|invoice_id|payment_id|txn_id|transaction_id|ticket_id|booking_id|doc_id|document_id|file_id|report_id|msg_id|message_id|chat_id|note_id|comment_id|post_id|task_id|project_id|team_id|org_id|group_id|cart_id|address_id|contract_id|app_id|request_id|ref|reference)=[0-9a-zA-Z-]+)' allurls.txt | sort -u > idor_candidates.txt
```

> Feed `idor_candidates.txt` straight into the BOLA testing steps from `API-Testing-Methodology.md` Phase 3 — swap the ID/UUID/param value while keeping your own auth token and check the response.

### 5.6 — GraphQL / Debug / Cloud Storage Leaks (bonus sweep)

```bash
# GraphQL endpoints
cat allurls.txt live_subs.txt | grep -Ei 'graphql|graphiql|/gql' | sort -u > graphql_endpoints.txt

# Cloud storage buckets referenced in URLs
cat allurls.txt | grep -EiP 's3\.amazonaws\.com|s3-[a-z0-9-]+\.amazonaws\.com|storage\.googleapis\.com|blob\.core\.windows\.net|digitaloceanspaces\.com' | sort -u > cloud_storage_refs.txt
```

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────────┐
│                    RECON WORKFLOW                          │
├──────────────────────────────────────────────────────────┤
│                                                              │
│  1. 🌐 Subdomain Enum (passive + active + permutations)    │
│            ↓                                                │
│  2. 🔎 Probe with httpx → live_subs.txt                     │
│            ↓                                                │
│  3. 🖧 IP Enum (ASN → CIDR → IPs → alive → ports → svc)     │
│            ↓                                                │
│  4. 🔁 rDNS on alive IPs → merge new subs → re-probe        │
│            ↓                                                │
│  5. 🕸️ Crawl + Passive URL Collection → allurls.txt          │
│            ↓                                                │
│  6. 🗂️ Dedup (uro) → split → params.txt / jsfiles.txt        │
│            ↓                                                │
│  7. 🎯 gf sort → sqli/xss/ssrf/lfi/rce/redirect/idor params │
│            ↓                                                │
│  8. 💎 Grep juicy subs, API subs, auth endpoints, IDOR IDs  │
│            ↓                                                │
│  9. 📝 Hand each list off to its testing phase              │
│                                                              │
└──────────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
Target has its own ASN (large org)?
    ├── YES → asnmap → mapcidr → alive IP scan → naabu/masscan → nmap
    └── NO  → skip ASN/CIDR route, rely on subdomain enum + httpx only

Need subdomains?
    ├── Passive fast pass    → subfinder / crt.sh / assetfinder / chaos
    ├── Deeper coverage      → amass passive + github-subdomains
    ├── Brute-force new ones → puredns / shuffledns
    └── Pattern-based new ones → gotator / alterx on known subs

Have live_subs.txt?
    ├── Want URLs/endpoints  → katana (active) + gau/waybackurls/gauplus (passive)
    └── Want juicy subs      → grep juicy-subdomain regex (Phase 5.2/5.3)

Have allurls.txt?
    ├── Want params for fuzzing     → params.txt → gf sort → *_params.txt
    ├── Want JS to mine              → jsfiles.txt → LinkFinder / manual grep
    ├── Want sensitive files         → interesting_files.txt regex (Phase 5.1)
    ├── Want auth flow targets       → auth_endpoints.txt regex (Phase 5.4)
    └── Want IDOR/BOLA candidates    → idor_candidates.txt regex (Phase 5.5)
```

---

### 📚 Resources & Custom Tools

- 🔗 [ProjectDiscovery Tool Suite](https://github.com/projectdiscovery) — subfinder, httpx, katana, dnsx, naabu, asnmap, mapcidr, urlfinder, alterx
- 🔗 [tomnomnom's tools](https://github.com/tomnomnom) — waybackurls, assetfinder, anew, gf
- 🔗 [ipscanner.sh — custom IP scanning script](https://github.com/scarsec1490/Bug-Hunting-Scripts/blob/main/ipscanner.sh)
- 🔗 [paramgrep.sh — custom param/gf sorting script](https://github.com/scarsec1490/Bug-Hunting-Scripts/blob/main/paramgrep.sh)
- 🔗 [Gf-Patterns](https://github.com/1ndianl33t/Gf-Patterns)
- Companion docs: `2FA-Bypass.md`, `API-Testing-Methodology.md`

---

<div align="center">

### 🔥 Map the surface wide. Filter it sharp. Hunt what's juicy.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
