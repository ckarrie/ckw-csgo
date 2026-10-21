# Contribution
Feel free to hack around and create pull requests.

# Contributors
Many thanks to
- iaN [@ifalatik](https://github.com/ifalatik) for keeping the code up-to-date

## Development

### 1. Create and activate a Python 3.10+ virtual environment
Django 5.1 requires Python 3.10 or newer (the project is developed on 3.13).

```shell
python3 -m venv wannspieltbig_dev
cd wannspieltbig_dev
source bin/activate        # Linux / macOS
.\Scripts\activate         # Windows
```

### 2. Install requirements
```shell
mkdir src
cd src
git clone https://github.com/ckarrie/ckw-csgo/
pip install -r ckw-csgo/requirements.txt
# install csgo app in editable mode (packaging is defined in ckw-csgo/pyproject.toml)
pip install -e ckw-csgo
```

### 3. Set up local Django project
```shell
django-admin startproject wsb
cd wsb/
mkdir static
nano wsb/settings.py
```

```python
# Change
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Add
    'django_vite',           # Add
    'rest_framework',        # Add
    'polymorphic',           # Add
    'csgomatches',           # Add
]

TEMPLATES = [
    {
        # ...
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'csgomatches.context_processors.games',  # Add
            ],
        },
    },
]

ROOT_URLCONF = 'csgomatches.urls'

LANGUAGE_CODE = 'de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

SITE_ID = 1

DJANGO_VITE = {
    "default": {
        "dev_mode": True,  # set False when on Production
        "manifest_path": BASE_DIR.parent / "ckw-csgo" / "csgomatches" / "static" / "manifest.json",
    }
}
```

#### Caching
No cache setup is needed for local development: Django's default `LocMemCache` is used, and all
`cache_page` timeouts are `0` while `DEBUG = True`.

Production uses memcached. To use it, install memcached (e.g. `sudo apt-get install memcached`) and add:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
    }
}
```

### 4. Setup Database and symlink static files

```shell
python wsb/manage.py migrate
python wsb/manage.py collectstatic -l
```

### 5. Add initial data

```shell
python wsb/manage.py shell
```

```python
# current Site
from django.contrib.sites.models import Site
Site.objects.filter(pk=1).update(domain='0.0.0.0', name='Local Dev')

# Add Team BIG
# `Team` is the legacy model (still used by the index view); `Organization` is its
# replacement for the new multi-game models. Create both for now.
from csgomatches.models import Team, Organization
Team(name='BIG').save()
Organization(name='BIG', slug='big').save()

# Add Admin User
from django.contrib.auth.models import User
User.objects.create_superuser(username="devuser", password="devuser", email="example@example.com")
```

### 6. Run Dev Server
```shell
python wsb/manage.py runserver 0.0.0.0:9001
```
Open Browser:
- Frontend: http://127.0.0.1:9001
- Django-Admin: http://127.0.0.1:9001/admin/

### 7. Run tests
```shell
python wsb/manage.py test csgomatches
```

---
# Frontend-Dev notes

The frontend assets are built with Vite and served through `django-vite` (already configured in
`INSTALLED_APPS` and `DJANGO_VITE` above).

### 1. Install node packages
```shell
cd ckw-csgo
npm install
```

### 2. Run dev server for development
```shell
npm run dev
```

### 3. Run this command for building (Remember to set `dev_mode` to `False` in settings.py)
```shell
npm run build
```
