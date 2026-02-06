# SaaS Execution Plan - Agent Solution BI

This document details the execution strategy for transforming the Agent Solution BI into a scalable SaaS platform.

## 📅 Overview

- **Start Date:** Immediate
- **Total Duration:** 12 Months
- **Phases:** 3 (Foundation, Growth, Maturity)

---

## 🏗️ Phase 1: Foundation (Months 1-3)
**Focus:** Infrastructure, Multi-tenancy, and Basic Security.

### 1.1 Containerization & Infrastructure (Weeks 1-2)
**Goal:** Establish a reproducible deployment environment.
- [ ] **Dockerize Backend:**
    - Create `backend/Dockerfile` using multi-stage builds (python:3.11-slim).
    - Configure `entrypoint.sh` for environment setup.
- [ ] **Dockerize Frontend:**
    - Create `frontend-solid/Dockerfile` (node:18 -> nginx:alpine).
    - Configure NGINX for SPA routing and reverse proxying to backend.
- [ ] **Orchestration:**
    - Create `docker-compose.yml` for local development (backend + frontend + redis + db).
    - Develop Helm charts for Kubernetes deployment (Deployment, Service, Ingress).
- [ ] **CI/CD:**
    - Set up GitHub Actions for automated build and test.
    - Implement semantic versioning.

### 1.2 Multi-Tenancy Basic (Weeks 3-4)
**Goal:** Isolate data per customer.
- [ ] **Data Model Update:**
    - Add `tenant_id` field to `User`, `Session`, and `Log` models.
- [ ] **Middleware:**
    - Implement `TenantMiddleware` in FastAPI to extract subdomains or headers.
    - Inject `tenant_id` into the request state.
- [ ] **Storage Isolation:**
    - Refactor `DataSourceManager` to accept `tenant_id`.
    - Implement logic to load `admmat.parquet` and `users.parquet` from dynamic paths (e.g., `s3://bucket/tenants/{tenant_id}/`).
- [ ] **Onboarding:**
    - Create a script/API to initialize a new tenant (folder structure, initial config).

### 1.3 Essential Security (Weeks 5-6)
**Goal:** Secure the application for public access.
- [ ] **Authentication Hardening:**
    - Switch `access_token` storage from localStorage to `HttpOnly; Secure; SameSite=Strict` cookies.
    - Implement CSRF protection middleware.
- [ ] **Token Management:**
    - Use Redis to store active session tokens and blacklist revoked tokens on logout.
- [ ] **Access Control:**
    - Enforce Strict RBAC.
    - Remove any "admin bypass" logic in `dependencies.py`.
- [ ] **Rate Limiting:**
    - Upgrade `slowapi` to use Redis backend.
    - Implement separate limits for authenticated vs. anonymous users.

### 1.4 Session & Scalability (Weeks 7-8)
**Goal:** Support multiple concurrent users stability.
- [ ] **Distributed Sessions:**
    - Replace file-based session storage with Redis.
    - Serialize agent memory/history to JSON/msgpack in Redis.
- [ ] **Database Pool:**
    - Increase DuckDB connection pool size (16+).
    - Investigate `duckdb.connect(readonly=True)` for read-heavy workloads.
- [ ] **Load Balancing:**
    - Configure NGINX as an ingress controller.
    - Set up health check endpoints (`/health`, `/ready`).

### 1.5 Basic Billing (Weeks 9-10)
**Goal:** Monetize the service.
- [ ] **Stripe Integration:**
    - Implement Stripe Checkout for subscription creation.
    - Handle webhooks for `invoice.paid`, `customer.subscription.deleted`.
- [ ] **Plan Logic:**
    - Define feature flags for Starter/Pro tiers.
    - Implement `QuotaService` to track and enforce usage limits (e.g., daily queries).

### 1.6 Observability (Weeks 11-12)
**Goal:** Know when things break.
- [ ] **Metrics:**
    - Expose Prometheus metrics (`/metrics`) from FastAPI.
    - Track: Request latency, 5xx errors, active LLM requests.
- [ ] **Logging:**
    - Ensure all logs are JSON formatted.
    - Integrate with a centralized logging solution (e.g., Loki/ELK setup).

---

## 🚀 Phase 2: Growth (Months 4-6)
**Focus:** Self-service and Expansion.

- **2.1 Self-Service Onboarding:** Automated signup, email verification, and instant provisioning.
- **2.2 White-labeling:** Dynamic theming (CSS variables) based on tenant configuration.
- **2.3 Public API:** Standardization of API V1, documentation with Redoc/Swagger, and API Key management.
- **2.4 Analytics:** New dashboard module for "Admin" role showing usage stats.
- **2.5 HA:** Database replication and CDN configuration.

---

## 🛡️ Phase 3: Maturity (Months 7-12)
**Focus:** Enterprise Requirements.

- **3.1 Compliance:** SOC 2 preparation, rigorous audit logging.
- **3.2 Advanced Features:** SSO (Keycloak/Auth0), Webhooks, Custom Integrations.
- **3.3 Performance:** Edge caching, GraphQL, specialized async workers for heavy LLM tasks.
- **3.4 Global Scale:** Multi-region deployment.
