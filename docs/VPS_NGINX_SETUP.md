# VPS Nginx Setup Guide

## 1. Update Server Name
Edit `/etc/nginx/sites-available/tuum.day`:

```nginx
server {
    listen 80;
    server_name hotdeal-api.tuum.day;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name hotdeal-api.tuum.day;
    
    # SSL Configuration (Cloudflare Origin CA)
    ssl_certificate /etc/ssl/cloudflare/certificate-origin.pem;
    ssl_certificate_key /etc/ssl/cloudflare/certificate-private.pem;
    
    # ... existing ssl settings ...
    
    location /api/ {
        proxy_pass http://localhost:10000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://localhost:10000;
    }
}
```

## 2. Apply Changes
Run: `sudo nginx -t && sudo systemctl reload nginx`
