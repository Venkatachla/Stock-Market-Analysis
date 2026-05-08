# 🔐 SECURITY CHECKLIST

**Use this checklist before each deployment and commit**

---

## ✅ PRE-COMMIT SECURITY CHECKLIST

Before committing any code:

- [ ] **No .env files committed**
  ```bash
  git status | grep ".env"  # Should be empty
  git ls-files | grep ".env"  # Should show only .env.example/.env.*.template
  ```

- [ ] **No hardcoded passwords/tokens**
  ```bash
  grep -r "password=" . --exclude-dir=.git --exclude-dir=node_modules --exclude="*.md"
  grep -r "dckr_pat_" . --exclude-dir=.git
  grep -r "api_key=" . --exclude-dir=.git
  ```

- [ ] **No database credentials**
  ```bash
  grep -r "mysql://" . --exclude-dir=.git
  grep -r "postgresql://" . --exclude-dir=.git
  ```

- [ ] **No AWS/Azure/GCP keys**
  ```bash
  grep -r "AKIA" . --exclude-dir=.git  # AWS keys
  grep -r "SecureString" . --exclude-dir=.git  # Azure
  ```

- [ ] **No JWT secrets in code**
  ```bash
  grep -r "SECRET_KEY=" . --include="*.py" --include="*.js" --exclude-dir=.git | grep -v "=${"
  ```

---

## ✅ PRE-PUSH SECURITY CHECKLIST

Before pushing to GitHub:

- [ ] **Review commits for secrets**
  ```bash
  git log --oneline origin/main..HEAD
  git show HEAD  # Review changes
  ```

- [ ] **Verify secrets are in GitHub Secrets**
  - [ ] DOCKER_USERNAME configured
  - [ ] DOCKER_PASSWORD configured  
  - [ ] KUBE_CONFIG_DATA configured

- [ ] **No .env files in staging**
  ```bash
  git status --short | grep ".env"  # Should be empty
  ```

- [ ] **Workflow uses GitHub Secrets**
  ```bash
  grep -n "secrets\." .github/workflows/docker-k8s-deploy.yml | grep -v "GITHUB_TOKEN"
  ```

---

## ✅ DEPLOYMENT SECURITY CHECKLIST

Before deploying to production:

- [ ] **GitHub Actions passed**
  - [ ] Build & Test ✅
  - [ ] SonarCloud ✅
  - [ ] Docker Build ✅
  - [ ] Docker Push ✅
  - [ ] Kubernetes Deploy ✅
  - [ ] Deployment Verification ✅

- [ ] **No security warnings**
  - [ ] GitHub Secret Scanning: PASS
  - [ ] Code Quality: No critical issues
  - [ ] Dependency Check: No vulnerabilities

- [ ] **Kubernetes secrets created**
  ```bash
  kubectl get secrets -n stockpulse
  kubectl get secret docker-registry-secret -n stockpulse
  ```

- [ ] **Environment variables properly set**
  ```bash
  kubectl get configmap -n stockpulse
  kubectl describe configmap stockpulse-config -n stockpulse
  ```

- [ ] **No secrets in pod logs**
  ```bash
  kubectl logs -n stockpulse <pod-name> | grep -i "password\|token\|secret"
  # Should return nothing
  ```

---

## 🔴 RED FLAGS - STOP IF YOU SEE THESE

NEVER commit or push if:

- [ ] 🚫 Real password visible in code
- [ ] 🚫 Docker token in documentation  
- [ ] 🚫 API key hardcoded in any file
- [ ] 🚫 `.env` file (without .example) in git
- [ ] 🚫 Private key (.pem, .key) in repository
- [ ] 🚫 kubeconfig file in repository
- [ ] 🚫 `docker login -u user -p password` in script
- [ ] 🚫 Credentials in commit message
- [ ] 🚫 Database password in docker-compose.yml
- [ ] 🚫 JWT secret in config file

**If you see any red flag:**
1. Stop immediately
2. Remove the secret
3. Use GitHub Secrets instead
4. Run security checks
5. Then commit/push

---

## 🛡️ SECRET HANDLING QUICK GUIDE

### Local Development
```bash
# Create from template (NOT committed)
cp .env.example .env

# Edit with YOUR values
# DO NOT commit .env
```

### Docker
```bash
# Use GitHub Secrets in workflow
uses: docker/login-action@v2
with:
  username: ${{ secrets.DOCKER_USERNAME }}
  password: ${{ secrets.DOCKER_PASSWORD }}

# NOT THIS:
# docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
```

### Kubernetes
```yaml
# Use Secret objects
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
data:
  password: <base64-encoded>

# Reference in deployment
env:
- name: PASSWORD
  valueFrom:
    secretKeyRef:
      name: app-secrets
      key: password
```

### GitHub Actions
```yaml
# Use ${{ secrets.NAME }}
- name: Deploy
  env:
    DATABASE_PASSWORD: ${{ secrets.DATABASE_PASSWORD }}
  run: |
    # Secrets automatically masked in logs
```

---

## 🔄 MONTHLY SECURITY REVIEW

Run monthly:

```bash
# Check for accidental commits
git log --all --oneline | grep -i "secret\|password\|key\|token" | head -20

# Check for common patterns
find . -type f -name "*.py" -o -name "*.js" | xargs grep -l "password.*=" | grep -v node_modules | grep -v ".git"

# Verify .gitignore is comprehensive
cat .gitignore | grep -E "env|secret|key|crt|pem"

# Check git config
git config --list | grep -i url
```

---

## 📞 INCIDENT RESPONSE

If a secret is accidentally committed:

### Immediate (< 1 hour)
1. **Stop everything** - Don't push or deploy
2. **Identify the secret** - What was exposed?
3. **Rotate the credential** - Generate new token/password
4. **Remove from git** - Use git filter-repo (advanced)
5. **Update GitHub Secrets** - With new credentials

### Short Term (< 1 day)
6. Notify team about incident
7. Review workflow for recurrence
8. Update documentation
9. Test deployment with new secrets

### Long Term
10. Post-mortem: How did this happen?
11. Prevent recurrence: Update .gitignore/pre-commit hooks
12. Audit for similar issues
13. Document the incident

---

## 📚 SECURITY RESOURCES

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [OWASP Secret Management](https://owasp.org/www-community/Credential_Management_Cheat_Sheet)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Kubernetes Security](https://kubernetes.io/docs/concepts/security/)
- [12 Factor App - Config](https://12factor.net/config)

---

## ✨ QUICK COMMANDS

```bash
# Check for secrets in current changes
git diff HEAD | grep -i "password\|secret\|token\|key"

# Check all files (be careful!)
git grep -i "password\|dckr_pat\|SECRET" -- '*.py' '*.js' '*.yaml' | grep -v "\.example" | grep -v ".template"

# Show what would be committed
git diff --cached

# Unstage file if accidentally staged
git reset <file>

# Remove from git history (if already committed)
git filter-repo --path <file> --invert-paths
git push origin --force-with-lease main

# Check if secrets in last N commits
git log --oneline -10
git show <commit-sha>

# Find files matching pattern
find . -name ".env*" -not -name ".env*.template" -not -name ".env.example"
```

---

*Security Checklist Version: 1.0*  
*Last Updated: May 8, 2026*  
*Status: ACTIVE*
