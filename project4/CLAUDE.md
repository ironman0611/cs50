# College Tracker — CLAUDE.md

## Project overview
CS50 Web Programming (CS50W) capstone project — **College Application Tracker**.
A Django web app where students can browse colleges, track application statuses, and manage application-related tasks.

**Django 5.2.12**, Python 3.11, SQLite3, Bootstrap 5 front-end.

## Key commands
```bash
# Start dev server
python manage.py runserver

# Run tests
python manage.py test tracker

# Create/apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (colleges are managed via admin)
python manage.py createsuperuser
```

## Architecture

```
capstone/          — Django project settings
  settings.py      — SQLite DB, Bootstrap via STATICFILES_DIRS (tracker/static)
  urls.py          — root URLs: admin/ + include('tracker.urls')

tracker/           — main app
  models.py        — College, Application, Task
  views.py         — 10 views (auth + CRUD + 2 JSON API endpoints)
  urls.py          — URL routing (see below)
  admin.py         — Custom admin with ApplicationAdmin + TaskInline
  context_processors.py — college_nav (injects nav_colleges into every template)
  static/          — CSS/JS (Bootstrap 5)
  templates/tracker/ — 7 HTML templates
```

## Data models

| Model | Key fields | Notes |
|---|---|---|
| **College** | name, location, application_deadline, website | Global catalogue, managed via Django admin |
| **Application** | user (FK → User), college (FK), status, notes | unique_together(user, college). Status: researching / applying / submitted / accepted / rejected / deferred |
| **Task** | application (FK → Application), title, description, completed, due_date | Sub-tasks per application |

## URL routes

| URL | View | Name | Auth |
|---|---|---|---|
| `/` | index | `index` | @login_required |
| `/colleges` | all_colleges | `all_colleges` | @login_required |
| `/my-colleges` | my_colleges | `my_colleges` | @login_required |
| `/apply` | apply_college | `apply_college` | @login_required, POST |
| `/my-colleges/remove/<id>` | remove_application | `remove_application` | @login_required, @require_POST |
| `/login` | login_view | `login` | public |
| `/logout` | logout_view | `logout` | public |
| `/register` | register | `register` | public |
| `/api/tasks/<app_id>` | get_tasks | `get_tasks` | @login_required, JSON |
| `/api/task/<id>/toggle` | toggle_task | `toggle_task` | @login_required, @csrf_exempt, PUT |

## Templates

| Template | Purpose |
|---|---|
| `layout.html` | Base HTML shell (Bootstrap 5, navbar, flash messages) |
| `base_app.html` | Extends layout, adds sidebar nav + main content area |
| `index.html` | Student dashboard with metrics and upcoming deadlines |
| `all_colleges.html` | Browse/search all colleges with pagination |
| `my_colleges.html` | User's tracked applications with search |
| `login.html` | Login form |
| `register.html` | Registration form |

## Notable implementation details

- **Authentication**: Custom login/register views using Django's built-in `User` model (no custom user model).
- **Pagination** on `all_colleges` view with configurable per_page (10, 20, all).
- **Search** by college name or location on both list pages.
- **Two JSON API endpoints** for task fetching and toggle (AJAX-driven).
- **Context processor** `college_nav` injects all colleges into every template for the sidebar quick-links.
- **No custom User model** — uses `django.contrib.auth.models.User`.
- **SQLite** database (`db.sqlite3` — in .gitignore).
- **No `.env` or environment variable loading** — `SECRET_KEY` is hardcoded in settings.py (acceptable for development/Course project but not production).

## Known gaps / future work
- Task create/edit API endpoints are incomplete (only get_tasks and toggle_task exist).
- No application status change endpoint — only apply/remove.
- `@csrf_exempt` on `toggle_task` — should use proper CSRF handling for PUT requests.
- `SECRET_KEY` should be moved to environment variables for production.
- No email notifications for deadlines.
