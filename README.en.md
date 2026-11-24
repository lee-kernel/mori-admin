<p align="center">
  <img src="web/public/logo.png" alt="Mori Logo" width="96" height="96" />
</p>

<h1 align="center">Mori</h1>

<p align="center">
  <a href="README.md">简体中文</a> | <strong>English</strong>
</p>

<p align="center">
  <a href="https://vuejs.org/"><img src="https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vuedotjs&logoColor=white" alt="Vue 3.5" /></a>
  <a href="https://antdv.com/"><img src="https://img.shields.io/badge/Ant%20Design%20Vue-4.2-1677FF?logo=antdesign&logoColor=white" alt="Ant Design Vue 4.2" /></a>
  <a href="https://www.typescriptlang.org/"><img src="https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white" alt="TypeScript 5.9" /></a>
  <a href="https://vite.dev/"><img src="https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite&logoColor=white" alt="Vite 5.4" /></a>
  <a href="https://nodejs.org/"><img src="https://img.shields.io/badge/Node.js-22-5FA04E?logo=nodedotjs&logoColor=white" alt="Node.js 22" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI 0.115" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12" /></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL 18" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Non--Commercial-red.svg" alt="License: Non-Commercial" /></a>
</p>

Mori is a Vue 3 + Ant Design Vue admin frontend framework designed to constrain how AI Agents build pages—keeping layouts, components, and styling consistent without drifting or pulling in extra UI libraries. It also ships with an optional FastAPI + PostgreSQL full-stack backend (authentication, optional 2FA, user groups, dynamic menus, operation permissions, and audit logs).

## What's Included

- **Fixed Component Boundary**: Strictly uses Vue 3, Ant Design Vue (registered on demand in `web/src/main.ts`), and built-in layout primitives (`PageLayout`, `PageFilterBar`, `TableSection`, `CardGridSection`, `PageState`).
- **Reference Page Patterns**: `web/src/view/patterns/` provides standard templates for workspace, card grid, detail page, modal/drawer forms, and state views alongside table and settings pages for direct reuse.
- **Static UI Gate (`npm run check:ui`)**: Verifies that no extra UI/CSS frameworks are introduced, all `<a-*>` tags are registered in `main.ts`, business views use `PageLayout` as root, and no hardcoded colors or `100vh` units exist.
- **Viewport & Theme Verification (`npm run verify:ui`)**: Automatically checks pages across desktop/mobile × light/dark combinations without a backend, detecting JS errors, failed requests, and horizontal overflow, with optional screenshot export.

## Documentation

- [AGENTS.md](AGENTS.md): Repository entry point and pre-commit checklist for Coding Agents
- [UI / UX Guidelines](docs/ui.md): Design principles, typography, theme tokens, components, and reference pages
- [AI Page Workflow](docs/ai-page-workflow.md): Prompt examples, generation workflow, and acceptance checklist
- [Backend Guidelines](docs/backend.md): Layering, API contract, SQL, and security conventions for the optional backend
- [Documentation Index](docs/README.md): Task-based guide directory

## Frontend-Only Preview

Run the pattern gallery and UI verification scripts directly under `web/` without PostgreSQL or the backend:

```bash
cd web
npm ci
npm run dev:preview                  # Start frontend-only preview (default http://127.0.0.1:5173)
npm run check:ui                     # Run static UI gate checks
npm run verify:ui                    # Verify all pattern pages (desktop/mobile x light/dark)
npm run verify:ui -- --screenshots   # Verify and save screenshots to web/.ui-verify/
```

Other common scripts: `npm run typecheck`, `npm run lint`, `npm run build`.

## Full-Stack Setup (Optional)

To use authentication, RBAC, dynamic menus, and audit logs, start the bundled FastAPI + PostgreSQL services.

### Docker Compose

1. Copy `.env.example` to `.env` in the repository root and set unique random values for `SECRET_KEY` and `POSTGRES_PASSWORD` (e.g., via `python -c "import secrets; print(secrets.token_hex(32))"`).
2. Run `docker compose up -d --build`. The API automatically initializes tables, menus, and permissions on first startup.
3. Run `docker compose exec api python -m app.create_admin` to set the `admin` password.
4. Visit `http://localhost:8080` to sign in (port configurable via `WEB_PORT`).

### Local Development

Requirements: Python 3.12, Node.js 22, and an empty PostgreSQL database.

```bash
# Backend (create a venv under api/ and configure api/.env)
python -m app.create_admin
python -m uvicorn app.main:app --host 127.0.0.1 --port 9394 --reload

# Frontend (under web/)
npm run dev
```

Open `http://127.0.0.1:5173` (Vite proxies `/api` to the backend). See [Module Development Guide](docs/module-development.md) for adding new business modules.

## Security

The optional full-stack backend includes the following built-in security controls:

- **Password & Session Security**: Passwords are SHA-256 digested client-side before transport and stored with salted PBKDF2-SHA256 (default 260,000 iterations). JWT sessions support immediate revocation via `token_version` (on logout, password change, role/status update, or 2FA reset) and temporary account lockout after repeated login failures.
- **Optional Two-Factor Authentication (2FA)**: Users can enable or disable standard TOTP (RFC 6238) 2FA under *Account → Security*. Enabling generates 8 one-time recovery codes stored as salted hashes. TOTP secrets are encrypted at rest with Fernet (optionally configured via `TOTP_ENCRYPTION_KEY`), two-step login challenge tokens are strictly isolated from access tokens, verification prevents code replay and counts toward lockout, and administrators can reset 2FA for non-default users.
- **Backend-Enforced RBAC & Auditing**: Dynamic menus only control frontend navigation; every protected endpoint enforces authentication and group-based operation permissions server-side. Login, failed login, logout, and sensitive management actions are logged with a server-generated `X-Trace-Id`.
- **Parameterized SQL & Startup Validation**: All raw SQL queries are fully parameterized. Startup checks enforce `SECRET_KEY` strength, `DEBUG=false` in production, valid CORS origins, and valid 2FA encryption key format, while logs and error responses redact secrets and tokens. See [Backend Guidelines](docs/backend.md#五安全与鉴权规范) for details.

## License

This project is licensed under the **Mori Non-Commercial License** (see [LICENSE](LICENSE)):

- **Permitted**: Personal learning, academic research, educational demonstration, and non-profit personal projects (with copyright and license notices retained).
- **Prohibited**: Any direct or indirect commercial use without prior written authorization from the copyright holder (including commercial product integration, enterprise internal production/operations, paid hosting/SaaS, or client deliverables).
- **Commercial Licensing**: Please contact the copyright holder via this repository for commercial authorization.
