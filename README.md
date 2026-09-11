# LegalDesk — Practice Management Platform

A polished, startup-grade legal practice management web app for advocates and chambers, built with Django + SQLite + hand-crafted HTML/CSS/JS (no frontend framework required).

Includes:
- A marketing **landing page** (hero, features, pricing, testimonials, CTA, footer)
- An **advocate workspace**: dashboard, case management, hearing tracking, internal notes, document vault, tasks, fee/billing records
- A separate, read-only **client portal** that only shows what an advocate marks as client-visible
- A clean custom design system (navy + gold palette, Inter + Source Serif fonts, responsive layout with a mobile sidebar)

## Quick start

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

python manage.py makemigrations dashboard
python manage.py migrate

# Populate realistic demo data (advocate + 2 clients + cases/hearings/tasks/fees)
python manage.py seed_demo

python manage.py runserver
```

Open **http://127.0.0.1:8000/** for the marketing homepage, or go straight to
**http://127.0.0.1:8000/login/**.

### Demo credentials (created by `seed_demo`)

| Role     | Username   | Password         |
|----------|-----------|------------------|
| Advocate | `advocate` | `Legal@Demo123` |
| Client   | `client`   | `Legal@Demo123` |

The advocate account is also a Django superuser, so you can open **/admin/** with the
same credentials to manage users, clients and raw records directly.

Run `python manage.py seed_demo --reset` to wipe and recreate the demo accounts and data.

## What's inside

```
legaldesk/            Project settings, root URLs, WSGI
dashboard/            The main app: models, views, forms, admin, urls
  management/commands/seed_demo.py   One-command realistic demo data
templates/            landing, login, dashboard, case list/detail, tasks,
                       fees, client portal, generic form, 403/404 pages
static/css/style.css  Full design system (variables, components, responsive)
static/js/app.js      Mobile sidebar, live search filter, confirm dialogs,
                       auto-dismissing flash messages
```

## Feature summary

- Django session-based authentication (`/login/`, `/logout/`)
- Two account types sharing one login screen: **advocates** and **clients**,
  separated automatically via a `ClientProfile` link
- **Cases**: create, list (search + status filter), detail view with
  overview, hearings, internal notes, linked tasks and documents
- **Hearings**: per-case, each flagged `client_visible` or advocate-only
- **Internal notes**: always private, never shown to clients
- **Documents**: file upload per case, each independently marked
  client-visible or private
- **Tasks**: assignable, prioritized (Low/Medium/High), due dates,
  overdue detection, one-click mark done/reopen
- **Fee records**: per case, paid/pending tracking, one-click toggle,
  running totals on the dashboard and fee list
- **Client portal**: a client only ever sees their own cases, and only the
  hearings/documents explicitly marked visible — no internal notes, no tasks,
  no other clients' data
- Custom 403 (access denied) and 404 pages
- Fully responsive: sidebar collapses to a slide-out drawer on mobile

## Important — this is still a demo/MVP

Before any real deployment for real clients or matters, you must add:
production-grade secrets management, HTTPS/SSL, a managed database (Postgres),
encrypted/managed file storage, audit logging, backups, a strong password
policy and 2FA, email/SMS notifications, malware/file scanning on uploads,
fine-grained role/permission policies (e.g. multi-advocate firms), applicable
privacy/legal compliance (e.g. Bar Council/data protection requirements), and
tested eCourts/API integrations only where officially permitted. Any AI/RAG
features should only be connected after data-retention and privacy controls
are explicitly defined.
