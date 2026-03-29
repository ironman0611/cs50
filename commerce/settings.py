    INSTALLED_APPS = [
        # ... other apps
        'tailwind',
        'theme',  # Replace 'theme' with your desired Tailwind app name
        'django_browser_reload',
    ]

    TAILWIND_APP_NAME = 'theme'  # Must match the name in INSTALLED_APPS
    INTERNAL_IPS = [
        "127.0.0.1",
    ]