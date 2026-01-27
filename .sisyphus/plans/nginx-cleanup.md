# Nginx Cleanup & Frontend Removal Plan

## Context

### Original Request
- **Goal**: Stop serving frontend files from the Nginx server (moved to Cloudflare).
- **Scope**:
  1. Modify Nginx configuration to remove static file serving.
  2. Delete deployed frontend files (`/var/www/hotdeal`).
  3. Keep Backend serving (`/api`, `/health`).
- **Constraint**: Do NOT delete `static/` from the repository (used for local dev & Cloudflare source).

### Metis Review
- **Guardrail**: Ensure `static/` in repo is preserved.
- **Risk**: Potential 404s if Cloudflare routing is misconfigured.

### Current Nginx Config (Reference)
```nginx
server {
    listen 80;
    server_name *.tuum.day tuum.day;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name hotdeal.tuum.day;
    # ... ssl config ...
    root /var/www/hotdeal;
    index index.html;
    # ... api proxy ...
    # Static files serving (TO REMOVE)
    location / {
        try_files $uri $uri.html $uri/ =404;
    }
}
```

---

## Work Objectives

### Core Objective
Clean up the production server by removing legacy frontend serving configuration and files, converting it to a pure API server.

### Concrete Deliverables
- Modified `/etc/nginx/sites-enabled/tuum.day`
- Deleted directory `/var/www/hotdeal`

### Definition of Done
- [ ] `curl https://hotdeal.tuum.day/api/health` returns 200 OK.
- [ ] `/var/www/hotdeal` does not exist on the server.
- [ ] `nginx -t` passes.

---

## Verification Strategy

### Manual Verification (Infrastructure)
**Execution Context**: All commands must be run via SSH on the production server.

1. **Config Check**: `sudo nginx -t`
2. **API Check**: `curl -I http://localhost:10000/health` (Backend running?)
3. **Proxy Check**: `curl -I https://hotdeal.tuum.day/health` (Nginx proxying?)

### Rollback Strategy
If `nginx -t` fails or the site becomes unreachable:
1. Restore backup: `sudo cp /etc/nginx/sites-enabled/tuum.day.bak /etc/nginx/sites-enabled/tuum.day`
2. Reload: `sudo systemctl reload nginx`

---

## TODOs

- [ ] 1. **Backup & Modify Nginx Configuration**
  
  **Execution Context**: Remote Server (SSH)

  **What to do**:
  1. **Backup**: `sudo cp /etc/nginx/sites-enabled/tuum.day /etc/nginx/sites-enabled/tuum.day.bak`
  2. **Edit**: `/etc/nginx/sites-enabled/tuum.day`
     - Remove `root /var/www/hotdeal;`
     - Remove `index index.html;`
     - Remove `location / { ... }` block entirely.
     - **Preserve**: `server_name`, `ssl_*`, `location /api/`, `location /health`.

  **Reference**:
  - See "Current Nginx Config" section above.

  **Acceptance Criteria**:
  - [ ] Backup file `/etc/nginx/sites-enabled/tuum.day.bak` exists.
  - [ ] `sudo nginx -t` returns "syntax is ok"
  - [ ] `sudo systemctl reload nginx` executes without error.

- [ ] 2. **Delete Legacy Frontend Files**

  **Execution Context**: Remote Server (SSH)

  **What to do**:
  - Remove the directory `/var/www/hotdeal`.
  - **WARNING**: Do NOT remove `static/` from the current directory (repository).

  **Acceptance Criteria**:
  - [ ] `ls /var/www/hotdeal` returns "No such file or directory"

---

## Success Criteria

### Final Checklist
- [ ] Nginx config is clean (no static serving).
- [ ] Backend (`/api`) is still accessible.
- [ ] Legacy files are gone.
- [ ] Backup exists (just in case).
