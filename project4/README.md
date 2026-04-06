# College Application Tracker

A small **Django 5** web app for browsing a college catalogue, saving schools to a personal list, tracking application status, and storing search preferences. Front end uses **Bootstrap 5**.

## Requirements

- Python 3.11+
- Django 5.2.x (install in a virtual environment)

## Setup

```bash
cd project4
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install "Django>=5.2,<6"
python manage.py migrate
python manage.py createsuperuser   # optional: manage colleges in /admin/
python manage.py runserver
```

Open **http://127.0.0.1:8000/** — register or log in, then use the dashboard, **All colleges**, **My colleges**, **Preferences**, and per-college detail pages (also linked from the sidebar).

## Common commands

| Command | Purpose |
|--------|---------|
| `python manage.py runserver` | Dev server |
| `python manage.py test tracker` | Run app tests |
| `python manage.py makemigrations` / `migrate` | Database changes |

Data is stored in **`db.sqlite3`** (ignored from git by default).

## Project layout

- **`capstone/`** — project settings and root URLs (`/admin/` + tracker).
- **`tracker/`** — models (`College`, `Application`, `UserProfile`, …), views, templates, static assets.

Staff users can add and edit **Colleges** in the admin; **Groups** and **Tasks** are not exposed in the admin UI.

## Production note

`DEBUG`, `SECRET_KEY`, and SQLite are suitable for local development only. Use environment-based settings, a production database, and HTTPS for a real deployment.
