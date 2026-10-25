# Spec: Network Access & Unified Ingress via NGINX Reverse Proxy

## Phase 0: Scope Check & Capability Map

Accessing the application from devices across the local network (LAN) currently fails during login and module navigation due to two coupled constraints: client-side hardcoded `localhost:8000` URLs and cross-origin (CORS) rejections. Resolving this via an NGINX reverse proxy unifies the network origin for both static web pages and API endpoints.

Because this change spans infrastructure, reverse proxy configuration, client HTTP adapter logic, and backend CORS configuration, we decompose it into the following capability map:

| Module ID | Responsibility | Depends On |
|---|---|---|
| `frontend-relative-client` | Adapt `httpClient.ts` and Next.js env configuration to safely support relative URLs without crashing `new URL()`. | — |
| `nginx-gateway` | Configure NGINX reverse proxy with routing for `/`, `/api/v1/`, and `/_next/webpack-hmr` WebSockets. | — |
| `docker-compose-orchestration` | Integrate `nginx:alpine` into `docker-compose.yml` with `host-gateway` resolution and healthchecks. | `nginx-gateway` |
| `backend-cors-alignment` | Update backend `CORSMiddleware` with `allow_origin_regex` and updated `.env` origins for direct LAN clients (e.g. Expo mobile). | — |

**Build & Execution Order:**  
`frontend-relative-client` → `nginx-gateway` → `docker-compose-orchestration` → `backend-cors-alignment`

---

## 1. Objective

Enable seamless network access to the SaaS Stock Deposit Control web application from any device on the local network (PC, laptop, tablet, mobile browser) by deploying an NGINX reverse proxy that consolidates frontend and backend under a single unified origin.

### Problem Statement
1. **Login Failure on Network:** `frontend-web/.env.local` sets `NEXT_PUBLIC_API_URL=http://localhost:8000`. When a network client opens `http://<LAN_IP>:3000`, the browser executes JavaScript that attempts to fetch `http://localhost:8000/api/v1/auth/login`. On remote devices, `localhost` resolves to the device itself where no server runs (`Failed to fetch`).
2. **CORS Violation:** If accessed from the host machine using its LAN IP (`http://192.168.1.5:3000`), the browser sends a cross-origin request to `http://localhost:8000`. The backend CORS whitelist (`CORS_ORIGINS`) rejects it because the IP origin is not listed.
3. **Apparent Module Routing Failure:** `DemoShell.tsx` guards all module routes (`/dashboard`, `/catalog`, `/audit`, `/reports`, `/users`). When unauthenticated, it immediately redirects the user to `/login`. To the user, clicking or navigating to different modules appears completely broken because every route bounces back to `/login`.

### Target Solution
Deploy an NGINX container that listens on port `8080` (or `80`) and acts as a single gateway:
- `http://<LAN_IP>:8080/` → Proxied to Next.js (`:3000`).
- `http://<LAN_IP>:8080/api/` → Proxied to FastAPI (`:8000`).
- `http://<LAN_IP>:8080/_next/webpack-hmr` → Proxied with WebSocket upgrade headers.
- Frontend web client makes relative API requests (`/api/v1/...`), ensuring **zero CORS issues** and **zero hardcoded IPs**.

---

## 2. Tech Stack

- **Reverse Proxy:** NGINX 1.25+ (`nginx:alpine`)
- **Container Orchestration:** Docker Compose v2 / Docker CLI
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript 5
- **Backend:** FastAPI, Python 3.12, Starlette `CORSMiddleware`
- **Database:** MariaDB 10.11 LTS (containerized)

---

## 3. Assumptions Surfaced Immediately

1. **Host Dev Services:** The Next.js development server (`frontend-web`) and FastAPI backend (`backend`) run on the host machine (e.g., via `npm run dev` and `uvicorn`), while MariaDB and NGINX run in Docker containers.
2. **Host-to-Container Bridge:** Docker on Linux supports reaching host services from inside a container via `host.docker.internal` using `extra_hosts: ["host.docker.internal:host-gateway"]`.
3. **Default Ingress Port:** NGINX will listen on port `8080` by default (configurable via `NGINX_PORT` in `.env`), avoiding conflicts with privileged port `80` or existing services on `3000`/`8000`.
4. **Mobile App Independence:** The React Native / Expo mobile app can continue calling the backend directly using `EXPO_PUBLIC_API_URL=http://<LAN_IP>:8000` or through NGINX `http://<LAN_IP>:8080`.

---

## 4. Commands

### Infrastructure Management (Docker Compose)
```bash
# Start infrastructure (MariaDB + NGINX)
docker-compose up -d

# Check running containers and health
docker-compose ps

# View NGINX logs
docker-compose logs -f nginx

# Stop infrastructure
docker-compose down
```

### Backend Dev Server (Host)
```bash
# Must bind to 0.0.0.0 or 127.0.0.1 (accessible to Docker host gateway)
backend/venv/bin/uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Dev Server (Host)
```bash
# Must bind to 0.0.0.0 so Docker host-gateway can reach it
cd frontend-web && npm run dev -- -H 0.0.0.0 -p 3000
```

### Verification & Testing
```bash
# 1. Healthcheck via NGINX proxy
curl -i http://localhost:8080/api/v1/health

# 2. Login via NGINX proxy
curl -i -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user_0@example.com","password":"password123"}'

# 3. Frontend Web unit tests
cd frontend-web && npm test
```

---

## 5. Project Structure

```
SaaSStockDepositControl/
├── docker/
│   ├── mariadb/
│   │   └── init-dbs.sql
│   └── nginx/
│       └── nginx.conf                 # [NEW] NGINX reverse proxy configuration
├── docker-compose.yml                 # [MODIFIED] Adds nginx service with host-gateway
├── .env                               # [MODIFIED] Adds NGINX_PORT, updates CORS_ORIGINS
├── .env.example                       # [MODIFIED] Documents NGINX_PORT and CORS_ORIGINS
├── backend/
│   └── api/
│       └── main.py                    # [MODIFIED] Adds allow_origin_regex for local LAN
├── frontend-web/
│   ├── .env.local                     # [MODIFIED] Sets NEXT_PUBLIC_API_URL=""
│   ├── .env.example                   # [MODIFIED] Documents NEXT_PUBLIC_API_URL=""
│   └── lib/
│       └── adapters/
│           ├── httpClient.ts          # [MODIFIED] Relative URL & safe URL resolution
│           └── httpClient.test.ts     # [MODIFIED] Tests for relative & absolute URLs
└── specs/
    └── SPEC-network-access-nginx-reverse-proxy.md  # [THIS SPEC]
```

---

## 6. Detailed Technical Specifications

### Capability 1: `frontend-relative-client`

#### 1.1 `frontend-web/lib/adapters/httpClient.ts`
When `NEXT_PUBLIC_API_URL` is empty, requests must be relative (`/api/v1/...`).
However, calling `new URL("/api/v1/...")` without a base throws a `TypeError: Invalid URL`. The client must safely resolve query params against a base origin without altering the relative path returned for `fetch`.

```typescript
export class HttpClient {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL ?? "") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  private buildUrl(path: string, params?: Record<string, string | number | boolean | null | undefined>): string {
    const isAbsolute = path.startsWith("http://") || path.startsWith("https://");
    const cleanPath = isAbsolute
      ? path
      : this.baseUrl
      ? `${this.baseUrl}/${path.replace(/^\/+/, "")}`
      : `/${path.replace(/^\/+/, "")}`;

    if (!params) {
      return cleanPath;
    }

    // Supply window.location.origin in browser, or fallback base for server/test environments
    const baseOrigin = typeof window !== "undefined" && window.location?.origin
      ? window.location.origin
      : "http://127.0.0.1:8080";

    const url = new URL(cleanPath, baseOrigin);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        url.searchParams.append(key, String(value));
      }
    });

    // If original path was relative, preserve relative pathname + search
    if (!isAbsolute && !this.baseUrl) {
      return `${url.pathname}${url.search}`;
    }

    return url.toString();
  }
  // ...
}
```

#### 1.2 `frontend-web/.env.local`
```env
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_DATA_SOURCE=api
```

---

### Capability 2: `nginx-gateway`

#### 2.1 `docker/nginx/nginx.conf`
```nginx
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    upstream frontend_upstream {
        server host.docker.internal:3000;
        keepalive 32;
    }

    upstream backend_upstream {
        server host.docker.internal:8000;
        keepalive 32;
    }

    server {
        listen 8080;
        server_name _;

        # Client body size limit for file uploads/audits
        client_max_body_size 20M;

        # 1. API Routing -> FastAPI backend
        location /api/ {
            proxy_pass http://backend_upstream;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection "";
            proxy_read_timeout 120s;
            proxy_connect_timeout 10s;
        }

        # 2. Next.js WebSockets & Hot Module Replacement (HMR)
        location /_next/webpack-hmr {
            proxy_pass http://frontend_upstream/_next/webpack-hmr;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 86400s;
        }

        # 3. Next.js Static Assets caching
        location /_next/static/ {
            proxy_pass http://frontend_upstream/_next/static/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # 4. Frontend Web Pages & Root
        location / {
            proxy_pass http://frontend_upstream;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

---

### Capability 3: `docker-compose-orchestration`

#### 3.1 `docker-compose.yml` Updates
```yaml
version: "3.8"

services:
  mariadb:
    image: mariadb:10.11
    container_name: saas-stock-mariadb
    restart: unless-stopped
    ports:
      - "${MARIADB_PORT:-3306}:3306"
    environment:
      MARIADB_ROOT_PASSWORD: "${MARIADB_ROOT_PASSWORD}"
      MARIADB_APP_PASSWORD: "${MARIADB_APP_PASSWORD}"
    env_file:
      - .env
    volumes:
      - mariadb_data:/var/lib/mysql
      - ./docker/mariadb/init-dbs.sql:/docker-entrypoint-initdb.d/01-init-dbs.sql:ro
    healthcheck:
      test: ["CMD", "mariadb-admin", "ping", "-h", "127.0.0.1", "--silent"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - backend-net

  nginx:
    image: nginx:alpine
    container_name: saas-stock-nginx
    restart: unless-stopped
    ports:
      - "${NGINX_PORT:-8080}:8080"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      mariadb:
        condition: service_healthy
    networks:
      - backend-net

volumes:
  mariadb_data:
    driver: local

networks:
  backend-net:
    driver: bridge
```

---

### Capability 4: `backend-cors-alignment`

#### 4.1 `backend/api/main.py`
In addition to explicit origins, allow regular expressions matching RFC-1918 private subnets and localhost to prevent CORS issues if clients access port 8000 directly:

```python
# CORS configuration
origins_str = os.getenv("CORS_ORIGINS", "*")
origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

# Regex to permit local development over private LANs (192.168.x.x, 10.x.x.x, 172.16-31.x.x, localhost)
local_network_regex = r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=local_network_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 4.2 `.env` and `.env.example`
```env
# ─── NGINX Proxy Gateway ───
NGINX_PORT=8080

# ─── CORS Origins ───
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8080,http://192.168.1.5:8080,http://192.168.1.5:3000
```

---

## 7. Testing Strategy

1. **Unit Tests (Frontend HTTP Client):**
   - Verify `HttpClient` handles relative URLs correctly without throwing `TypeError`.
   - Verify query parameters are properly attached to relative paths (`/api/v1/articles?page=1&limit=10`).
   - Run: `npm test` in `frontend-web`.

2. **Integration Tests (Proxy Gateway):**
   - Probe `http://localhost:8080/api/v1/health` through NGINX and verify `HTTP 200`.
   - Probe `http://localhost:8080/` through NGINX and verify HTML payload from Next.js.
   - Execute authentication `POST http://localhost:8080/api/v1/auth/login` and verify signed JWT response.

3. **End-to-End LAN Verification:**
   - From a secondary device on the WiFi/LAN (e.g., smartphone), open `http://<LAN_IP>:8080`.
   - Log in with `user_0@example.com` / `password123`.
   - Verify redirection to `/dashboard`.
   - Click each module link in the sidebar (`/catalog`, `/audit`, `/reports`, `/users`).
   - Verify that data renders and that `DemoShell` does not redirect to `/login`.

---

## 8. Boundaries

### Always Do
- Ensure all frontend API calls use relative paths (`/api/v1/...`) when behind the reverse proxy.
- Maintain `extra_hosts: ["host.docker.internal:host-gateway"]` in Docker Compose for Linux compatibility.
- Keep `proxy_http_version 1.1` and WebSocket upgrade headers for Next.js HMR stability.
- Run `npm test` in `frontend-web` before marking implementation complete.

### Ask First
- Changing the default external gateway port from `8080` to `80`.
- Moving `backend` and `frontend-web` completely into containerized services in `docker-compose.yml`.

### Never Do
- Hardcode LAN IP addresses (e.g., `192.168.1.5`) into client-side code or git-committed frontend constants.
- Disable authentication checks or remove `<DemoShell>` route guards.
- Bypass `CORSMiddleware` with unsafe permissive origins without credentials awareness.

---

## 9. Success Criteria

- [ ] NGINX container is running healthy in Docker via `docker-compose up -d`.
- [ ] Navigating to `http://<LAN_IP>:8080` loads the Next.js login screen from any network device.
- [ ] Submitting credentials on the login screen authenticates successfully without CORS or fetch errors.
- [ ] Redirection to `/dashboard` succeeds, and user data is rendered.
- [ ] Navigation between `/catalog`, `/audit`, `/reports`, and `/users` operates smoothly without bouncing to `/login`.
- [ ] All 34 existing frontend tests pass in `npm test`.

---

## 10. Implementation Plan & Tasks

### Task 1: Update Frontend HTTP Client for Relative URLs
- **Files:** `frontend-web/lib/adapters/httpClient.ts`, `frontend-web/lib/adapters/httpClient.test.ts`, `frontend-web/.env.local`, `frontend-web/.env.example`
- **Acceptance:** `HttpClient` accepts empty `baseUrl`, supports relative URLs with query parameters safely, all unit tests pass.
- **Verification:** `cd frontend-web && npm test`

### Task 2: Create NGINX Configuration & Add to Docker Compose
- **Files:** `docker/nginx/nginx.conf`, `docker-compose.yml`, `.env`, `.env.example`
- **Acceptance:** `nginx` service added to `docker-compose.yml` with port 8080 and host gateway; `docker-compose up -d` starts `saas-stock-nginx`.
- **Verification:** `docker-compose ps` shows `saas-stock-nginx` Up.

### Task 3: Align Backend CORS with LAN Subnets
- **Files:** `backend/api/main.py`, `.env`, `.env.example`
- **Acceptance:** Backend accepts CORS requests from LAN IPs and port 8080.
- **Verification:** `curl -i -X OPTIONS http://localhost:8000/api/v1/health -H "Origin: http://192.168.1.5:8080" -H "Access-Control-Request-Method: GET"` returns `Access-Control-Allow-Origin`.

### Task 4: End-to-End Verification & Health Checks
- **Files:** `scripts/devops/deploy.sh`
- **Acceptance:** End-to-end proxy requests verify `/` and `/api/v1/health`.
- **Verification:** `curl -i http://localhost:8080/api/v1/health` returns HTTP 200.
