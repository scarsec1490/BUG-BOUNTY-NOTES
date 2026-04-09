
---

## 📁 1. Find Sensitive Directories

```bash
subfinder -d example.com -silent | while read host; do
    for path in /config.js /config.json /app/config.js /settings.json /database.json /firebase.json /.env /.env.production /api_keys.json /credentials.json /secrets.json /google-services.json /package.json /package-lock.json /composer.json /pom.xml /docker-compose.yml /manifest.json /service-worker.js; do
        echo "$host$path"
    done
done | httpx -mc 200
```

---

## 📄 2. Find Interesting Files

```bash
cat allurls.txt | grep -E "\.(xls|xml|xlsx|json|pdf|sql|doc|docx|pptx|txt|zip|tar\.gz|tgz|bak|7z|rar|log|cache|secret|db|backup|yml|gz|config|csv|yaml|md|md5|tar|xz|7zip|p12|pem|key|crt|csr|sh|pl|py|java|class|jar|war|ear|sqlitedb|sqlite3|dbf|db3|accdb|mdb|sqlcipher|gitignore|env|ini|conf|properties|plist|cfg)$"
```

---

## 🌐 3. Find Interesting Domains

```bash
grep -Ei "admin|administrator|panel|dashboard|manage|control|api|rest|graphql|v[0-9]+|dev|test|testing|stage|staging|qa|uat|preprod|sandbox|login|signin|signup|auth|sso|oauth|account|user|profile|session|token|jwt|verify|reset|password|otp|mfa|2fa|cdn|static|media|assets|files|storage|upload|download|bucket|s3|blob|old|backup|bak|legacy|archive|copy|clone|monitor|monitoring|status|health|metrics|alert|grafana|prometheus|kibana|elastic|logs|debug|trace|tmp|cache|error|dump|aws|gcp|azure|cloud|k8s|docker|jenkins|ci|cd|git|gitlab|github|bitbucket|service|gateway|proxy|edge|backend|billing|payment|invoice|order|cart|wallet|transaction|internal|private"
```

---

## 🌐 4. Find Leaked Credentials

```bash
https://virustotal.com/vtapi/v2/domain/report?apikey=VIRUSTOTAL-API-KEY&domain=TARGET.com
```

---

