# College Application Tracker

College Application Tracker is a Django web application that helps students organize college research and application progress in one place. Instead of juggling spreadsheets and bookmarks, users can browse a searchable college catalog, save schools to a personal list, and update each school's application status over time. The app supports account-based workflows, so each student sees only their own saved data and preferences.

The main user flow is: register/login, discover colleges from the full catalog, add interesting colleges to "My Colleges," and then track status changes (for example, planning, applied, accepted, or rejected). In addition, each user can store preference filters (such as state, tuition range, and other profile-friendly constraints) to make repeated searching faster and more personalized. The interface is intentionally simple and mobile friendly, using Bootstrap styling with a custom CSS/JS layer for app-specific interactions.

## Distinctiveness and Complexity

This project satisfies CS50W distinctiveness and complexity requirements for several reasons:

- It is not a copy of the course's social network, commerce, wiki, or mail projects. The domain problem is different: multi-step college application planning.
- It combines authentication, relational data modeling, personalized user preferences, and status-tracking behavior in a single product flow.
- The data model goes beyond a single content table: colleges are global objects, while applications/profiles are user-specific and linked through relationships.
- The UI includes multiple pages with context-specific behavior (catalog browsing, saved list management, detail pages, and preference editing), not just CRUD on one model.
- The project balances both backend logic (Django models/views/routing/forms/admin) and frontend behavior (templating, Bootstrap layout, custom JS/CSS), demonstrating full-stack complexity.

## What each file contains

Top-level project files:

- `manage.py`: Django management entry point for running the server, migrations, tests, and admin tasks.
- `README.md`: project writeup and setup instructions.
- `requirements.txt`: Python package dependencies required to run the project.

Project configuration (`capstone/`):

- `capstone/settings.py`: Django settings (installed apps, templates, database, static, auth redirects, etc.).
- `capstone/urls.py`: root URL routing (admin site + tracker app routes).
- `capstone/asgi.py` and `capstone/wsgi.py`: deployment entry points for ASGI/WSGI servers.
- `capstone/__init__.py`: package marker.

Main app (`tracker/`):

- `tracker/models.py`: data models such as `College`, `Application`, and `UserProfile`.
- `tracker/views.py`: request handlers for dashboard, catalog, saved colleges, college detail, auth flow, and preferences.
- `tracker/urls.py`: app-specific routes mapped to tracker views.
- `tracker/admin.py`: Django admin registrations and admin-side model configuration.
- `tracker/apps.py`: app configuration metadata.
- `tracker/signals.py`: model signal handlers (used for profile and related automation).
- `tracker/context_processors.py`: shared template context data (for global UI state).
- `tracker/tests.py`: app tests.
- `tracker/migrations/`: schema migration history.
- `tracker/templates/tracker/`: all HTML templates for pages and reusable partials.
- `tracker/static/tracker/css/styles.css`: custom styling.
- `tracker/static/tracker/js/app.js`: client-side interactivity.

## How to run the application

1. Open a terminal in the project directory:

   - `cd <where you clone the repo>`

2. Create and activate a virtual environment:

   - `python -m venv .venv`
   - macOS/Linux: `source .venv/bin/activate`
   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`

3. Install dependencies:

   - `pip install -r requirements.txt`

4. Apply database migrations:

   - `python manage.py migrate`

5. (Optional) Create an admin user:

   - `python manage.py createsuperuser`

6. Start the development server:

   - `python manage.py runserver`

7. Open:
   - `http://127.0.0.1:8000/`

## Additional information for staff

- Database: local development uses SQLite (`db.sqlite3`), which is generated after migrations.
- Admin access: staff/superuser accounts can manage college records from `/admin/`.
- Scope note: this project is designed for local development and demonstration; production deployment would require environment-based secrets, hardened settings, and a production-grade database.
- Testing: run `python manage.py test tracker` to execute automated tests.
