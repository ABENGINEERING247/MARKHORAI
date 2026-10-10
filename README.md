# MARKHOR AI — Centralized Master-Agent Application

MARKHOR AI is a Streamlit application with a single OpenAI-powered master agent, a registry of 200 specialist agent definitions, private accounts, per-user memory, chat history, task scheduling, and an optional notification worker.

## Features

- Master Agent Markhor routes prompts to 200 specialist roles (8 categories × 25 agents).
- OpenAI-powered natural-language routing and response generation.
- User registration and sign-in; salted PBKDF2 password hashes.
- Per-user chat history, tasks, and saved memory, with user-scoped database queries.
- Create, complete, delete, and review reminders.
- Browser notification permission prompt while the Streamlit page is open.
- Optional `ntfy` push notifications delivered by a separate persistent worker.
- SQLAlchemy database layer: local SQLite for development and managed PostgreSQL for multi-user cloud deployment.

## Important limitations

1. The 200 agents are specialist definitions routed by Markhor, not 200 independent always-running AI services. External actions require tools/integrations to be configured.
2. Browser notifications work only where the browser supports them, permission is granted, and the page/browser environment allows them. This starter does not implement a full Web Push/VAPID service worker.
3. For reminders to fire while the Streamlit app is closed or hibernating, run `worker.py` on an always-on worker service and configure `NTFY_TOPIC`. Install the ntfy mobile app and subscribe to that private topic. A worker is not run reliably inside Streamlit Community Cloud.
4. Community Cloud's local filesystem is not a durable multi-user database. Configure `DATABASE_URL` to managed PostgreSQL before sharing this app publicly. The SQLite fallback is for local development only.
5. This starter is not yet an enterprise identity system: add email verification, password recovery, login throttling, account deletion/export controls, and security review before public production use.
6. Do not use public notification topics for private/sensitive reminder content.

## Project layout

```text
markhor_ai/
├── app.py
├── worker.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   ├── config.toml
│   └── secrets.example.toml
└── markhor/
    ├── __init__.py
    ├── agents.py
    ├── ai.py
    ├── db.py
    ├── notifications.py
    └── security.py
```

## Run locally

Python 3.11 or 3.12 is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` based on `.streamlit/secrets.example.toml`, then set your real `OPENAI_API_KEY`. Keep `secrets.toml` out of Git. For local testing, the app can use SQLite; for multiple users and durable storage, configure `DATABASE_URL` to PostgreSQL.

```bash
streamlit run app.py
```

To test the notification worker locally, set `NTFY_TOPIC` in the environment, install/subscribe to the same private topic in ntfy, and run in another terminal:

```bash
python worker.py
```

## Deploy the Streamlit UI

1. Create a GitHub repository and upload the project files. Do **not** upload `.streamlit/secrets.toml`, database files, or API keys.
2. Provision a managed PostgreSQL database (for example, Neon or Supabase) and copy its SSL-enabled connection URL.
3. Open [Streamlit Community Cloud](https://share.streamlit.io/), choose **Create app**, select your repository/branch, and set the entrypoint to `app.py`.
4. In app settings, add secrets similar to the following (replace every placeholder):

```toml
OPENAI_API_KEY = "your-real-openai-api-key"
OPENAI_MODEL = "gpt-4o-mini"
DATABASE_URL = "postgresql://user:password@host:5432/database?sslmode=require"
```

5. Deploy and test account creation, sign-in, agent routing, memory isolation, and reminder creation with separate test accounts.

Official Streamlit instructions: [Community Cloud deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [Secrets management](https://docs.streamlit.io/deploy/concepts/secrets).

## Deploy persistent reminders

Deploy `worker.py` as a separate, always-on Python worker on a host that supports long-running processes (for example, a worker service on a cloud platform). Give it the same `DATABASE_URL` and a private `NTFY_TOPIC`. Install the ntfy mobile app on each device and subscribe to the topic. The worker polls every 20 seconds by default (`MARKHOR_POLL_SECONDS` can change this).

**Important:** this simple worker is a starter, not a high-availability queue. Run exactly one worker per database unless you add locking/claim semantics. Failed deliveries remain `due` and are not automatically marked sent. Add retries, monitoring, rate limits, and an authenticated per-user subscription design before production.

## Browser notifications

The browser notification control asks for permission and demonstrates a notification while the page is open. It is not a full standards-based web-push implementation. Real push while the browser is closed requires a service worker, VAPID keys, a subscription endpoint, and a push sender; the ntfy integration is the included cross-device alternative.

## OpenAI costs and privacy

OpenAI API usage is billed separately by OpenAI. Set an appropriate model, monitor usage, and apply budget limits in your OpenAI account. Prompts are sent to the configured OpenAI API for processing. Do not save sensitive personal information unless you have a suitable privacy and retention policy.

## Before production

- Use HTTPS and managed PostgreSQL backups.
- Add email verification, password reset, login throttling, CSRF/rate-limit protections, and admin controls.
- Add explicit per-agent tool permissions and approval gates before any external side effects.
- Configure private push subscriptions per user instead of a shared topic for confidential reminders.
- Add scheduler locks, retry/backoff, delivery receipts, monitoring, and timezone/recurrence tests.
- Review legal/privacy obligations for your users and deployment region.
