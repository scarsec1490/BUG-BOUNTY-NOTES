# 🛰️ FOFA Dorking Master List - Bug Bounty

Copy & paste ready FOFA queries for reconnaissance and vulnerability hunting.

---

# 📚 BASIC SYNTAX

```bash
title="..."           # Page title
body="..."            # Page content  
header="..."          # HTTP headers
domain="..."          # Domain
host="..."            # Hostname
ip="..."              # IP
port="..."            # Port
protocol="..."        # http/https
server="..."          # Server software
app="..."             # Application
cert="..."            # SSL certificate
country="..."         # Country
region="..."          # Region
city="..."            # City
os="..."              # OS
icon_hash="..."       # Favicon hash
extension="..."       # File extension
path="..."            # URL path

# Operators
&& (AND) | || (OR) | ! (NOT)
```

---

# 🔐 1. LOGIN & ADMIN PANELS

```bash
title="admin" && port="443"
title="Login" && country="US"
title="后台登录"
title="管理后台"
title="Administrator Login"
title="Dashboard"
title="Control Panel"
title="Welcome to nginx" && header="admin"
body="admin login" && port="8080"
body="admin panel" && protocol="https"
path="/admin" && status_code="200"
path="/login" && port="443"
path="/wp-admin"
path="/administrator"
path="/admin.php"
path="/manage"
path="/console"
path="/dashboard"
```

---

# ⚙️ 2. ENVIRONMENT & CONFIG FILES

## 🌱 ENV FILES
```bash
path=".env"
path=".env.production"
path=".env.local"
path=".env.dev"
path=".env.staging"
path=".env.example"
body="APP_ENV" && body="DB_PASSWORD"
body="APP_KEY" && body="APP_ENV=production"
```

## ⚙️ CONFIG FILES
```bash
path="config.php"
path="wp-config.php"
path="configuration.php"
path="config.inc.php"
path="config.json"
path="config.yml"
path="application.properties"
path="application.yml"
path="settings.py"
path="local_settings.py"
body="database.php"
body="db_config"
body="database.yml"
body="appsettings.json"
body="secrets.json"
body="credentials.json"
body="service-account.json"
```

## 🧬 GIT EXPOSURE
```bash
path=".git/config"
path=".git/HEAD"
path=".git/index"
body=".git/config" && port="80"
```

---

# 🗄️ 3. DATABASE CONNECTION STRINGS

## MySQL
```bash
body="mysql://"
body="mysql+pymysql://"
body="jdbc:mysql://"
body="DB_CONNECTION=mysql"
body="MYSQL_PASSWORD"
body="MYSQL_DATABASE"
```

## PostgreSQL
```bash
body="postgresql://"
body="jdbc:postgresql://"
body="PGPASSWORD"
body="POSTGRES_PASSWORD"
body="DATABASE_URL=postgres"
```

## MongoDB
```bash
body="mongodb://"
body="mongodb+srv://"
body="mongo://"
body="MONGO_PASSWORD"
body="MONGODB_URI"
```

## Redis
```bash
body="redis://"
body="REDIS_PASSWORD"
```

## SQL Server
```bash
body="sqlserver://"
body="jdbc:sqlserver://"
body="Server=" && body="Database="
```

---

# 🔑 4. API KEYS & TOKENS

## Generic
```bash
body="api_key"
body="api-secret"
body="api_token"
body="access_token"
body="auth_token"
body="secret_key"
```

## JWT
```bash
body="eyJ" && length(body)>200
```

## AWS
```bash
body="AKIA"
body="aws_access_key_id"
body="aws_secret_access_key"
body="AWS_ACCESS_KEY_ID"
body="AWS_SECRET_ACCESS_KEY"
```

## Google
```bash
body="AIza" && length(body)>30
body="GOOGLE_API_KEY"
body="service_account.json"
```

## Stripe
```bash
body="sk_live_"
body="pk_live_"
```

## GitHub
```bash
body="ghp_" && length(body)>30
```

## Slack
```bash
body="xoxb-"
body="xoxp-"
```

---

# ☁️ 5. CLOUD PROVIDERS

```bash
body="s3.amazonaws.com"
body="amazonaws.com"
body="cloud.google.com"
body="blob.core.windows.net"
body="azurewebsites.net"
body="digitaloceanspaces.com"
body="aliyuncs.com"
```

---

# 🔒 6. PRIVATE KEYS & CERTIFICATES

```bash
body="BEGIN RSA PRIVATE KEY"
body="BEGIN OPENSSH PRIVATE KEY"
body="BEGIN PRIVATE KEY"
body="BEGIN CERTIFICATE"

path=".ssh/id_rsa"
path=".ssh/authorized_keys"

extension="pem"
extension="key"
extension="pfx"
```

---

# 🚀 7. CI/CD & DEPLOYMENT

```bash
path=".github/workflows"
path=".gitlab-ci.yml"
header="Jenkins"
path="Dockerfile"
path="docker-compose.yml"
path="deployment.yaml"
path="terraform.tfvars"
path="ansible.cfg"
```

---

# 🏠 8. INTERNAL & STAGING

```bash
host="*.internal.*"
host="*.dev.*"
host="*.staging.*"
host="*.test.*"

body="192.168."
body="10.0."
body="127.0.0.1"

path="/internal"
path="/debug"
path="/swagger"
path="/graphql"
path="/phpinfo.php"
```

---

# 📁 9. SENSITIVE FILE TYPES

```bash
extension="sql"
extension="bak"
extension="backup"
extension="zip"

extension="log"
path="/logs"

extension="db"
extension="sqlite"

extension="rar"
extension="7z"
```

---

# ⚡ 10. ONE-LINER QUICK WINS

```bash
title="admin" && !title="login"
path=".env" && body="production"
body="AKIA" && extension="php"
body="BEGIN RSA PRIVATE KEY"
path="/phpmyadmin" && status_code="200"
body="mongodb+srv://" && body="password"
body="eyJ" && length(body)>500
extension="pem" && body="PRIVATE"
host="*.staging.*" && port="443"
```

---

# 🎯 TARGET-SPECIFIC

```bash
domain="target.com" && path=".env"
domain="target.com" && body="password"
domain="target.com" && path="/admin"
domain="target.com" && extension="pem"
domain="target.com" && body="AKIA"
domain="target.com" && path="/.git/config"
```

---

# ➕ ADD NEW DORK TEMPLATE

```md
### 🔎 Dork Name

```bash
your dork here
```

**📌 Description:**  
**🎯 Use Case:**  

---
```

---

# ⚠️ DISCLAIMER

For educational and authorized testing only.
