# TLS Termination — nginx reverse proxy

Production: TLS на reverse proxy, приложение слушает HTTP внутри сети.

## Схема

```
Client (HTTPS) → nginx (443) → support-agent:8000 (HTTP)
```

## Пример nginx

```nginx
upstream support_agent {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name support.example.com;

    ssl_certificate     /etc/letsencrypt/live/support.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/support.example.com/privkey.pem;

    # Security headers (app also sets some; avoid duplicates in prod)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://support_agent;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE / streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}

server {
    listen 80;
    server_name support.example.com;
    return 301 https://$host$request_uri;
}
```

## Docker Compose (staging → production-like)

Добавьте сервис `nginx` перед `app`, пробросьте только 443 наружу; `app` без `ports` на хост.

## Чеклист

- [ ] Сертификаты (Let's Encrypt / ACM)
- [ ] `CORS_ORIGINS` — только HTTPS-домены виджета
- [ ] `API_KEYS` и `ADMIN_API_KEY` заданы
- [ ] Health check: `GET /health` через proxy
- [ ] SSE: `proxy_buffering off` для `/chat/stream`

См. также [SECURITY.md](SECURITY.md), [RUNBOOK.md](RUNBOOK.md).
