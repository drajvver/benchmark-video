# Deployment Guide

You can deploy the Video Benchmark platform in several ways. The simplest uses pre-built Docker images and a free hosted PostgreSQL database.

---

## Option 1: Pre-built Images + Free Supabase DB (Easiest)

### 1. Get a free PostgreSQL database

**Supabase** (recommended — free tier includes 500 MB):
1. Sign up at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **Project Settings → Database → Connection String**
4. Copy the **URI** format string (starts with `postgresql://`)
5. Add `?sslmode=require` to the end if not present

**Neon** (alternative — free tier includes 500 MB):
1. Sign up at [neon.tech](https://neon.tech)
2. Create a project and copy the connection string

### 2. Create an environment file

```bash
cp .env.deploy.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.XXXXXXXXXXXXXXXX.supabase.co:5432/postgres?sslmode=require
SECRET_KEY=$(openssl rand -hex 32)
```

### 3. Deploy

```bash
# Using pre-built images from GitHub Container Registry
docker compose -f docker-compose.ghcr.yml up -d

# Or build locally from source
docker compose -f docker-compose.deploy.yml up -d --build
```

### 4. Access

Open `http://your-server-ip` in a browser. The backend API is available at `http://your-server-ip/api/v1/`.

---

## Option 2: Self-hosted (Docker Compose with local Postgres)

For local development or a server where you want everything in one place:

```bash
docker compose up -d
```

This runs PostgreSQL, backend, and frontend all in one stack.

---

## Option 3: Separate Frontend Hosting (CDN)

If you want to host the frontend on a static host (Cloudflare Pages, Vercel, GitHub Pages) and the backend on a VPS:

### Backend only

```yaml
# docker-compose.backend-only.yml
services:
  backend:
    image: ghcr.io/drajvver/benchmark-video-backend:latest
    environment:
      DATABASE_URL: ${DATABASE_URL}
      SECRET_KEY: ${SECRET_KEY}
      CORS_ORIGINS: '["https://your-frontend-domain.com"]'
    ports:
      - "8000:8000"
```

### Frontend build

```bash
cd web/frontend
npm ci
VITE_API_URL=https://api.your-domain.com/api/v1 npm run build
```

Deploy the `dist/` folder to your static host.

---

## Updating

```bash
# Pull latest images
docker compose -f docker-compose.ghcr.yml pull

# Restart with new images
docker compose -f docker-compose.ghcr.yml up -d
```

---

## SSL / HTTPS

For production, put a reverse proxy in front. Options:

- **Caddy** (easiest — auto HTTPS):
  ```
  your-domain.com {
      reverse_proxy localhost:80
  }
  ```

- **Nginx + Certbot** (traditional)

- **Cloudflare Tunnel** (free, no open ports needed)

---

## Troubleshooting

**"Connection refused" to database:**
- Check your `DATABASE_URL` is correct
- Ensure the database allows connections from your server's IP (Supabase: **Project Settings → Database → IPv4** or use **Connection Pooler**)

**CORS errors in browser:**
- Set `CORS_ORIGINS` to include your frontend domain, e.g., `["https://bench.example.com"]`

**Tables not created:**
- The backend auto-creates tables on startup via `create_db_and_tables()`
- Check backend logs: `docker compose -f docker-compose.ghcr.yml logs backend`
