# Contribution
Feel free to hack around and create pull requests.

## Developement

### 1. Create and activate Python 3.5.x virtual environment
```shell
python3 -m venv wannspieltbig_dev
cd wannspieltbig_dev
source bin/activate
```

### 2. Install requirements
```
beautifulsoup4==4.8.1
bs4==0.0.1
Django==2.2.7
django-ical==1.7.0
django-recurrence==1.10.1
djangorestframework==3.10.3
icalendar==4.0.4
python-dateutil==2.8.1
python-memcached==1.59
python-telegram-bot==12.2.0
python-twitter==3.5
requests==2.22.0
```

### 3. Create your local Django project
```shell
django-admin startproject wsb
```

### 4. Install csgo-App
```shell
mkdir src
cd src
git clone https://github.com/ckarrie/ckw-csgo/
pip install -e ckw-csgo
```

### 5. Edit settings.py / add to INSTALLED_APPS

```shell
cd wannspieltbig_dev/
mkdir wsb/static
nano wsb/wsb/settings.py
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
    'rest_framework',        # Add
    'csgomatches',           # Add
]

ROOT_URLCONF = 'csgomatches.urls'

LANGUAGE_CODE = 'de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = '/home/christian/workspace/venvs/wannspieltbig_dev/wsb/static'  # CHANGE TO YOUR LOCAL FOLDER
```

### 6. Setup Database and symlink static files

```shell
python wsb/manage.py migrate
python wsb/manage.py collectstatic -l
```

### 7. Add initial data

```shell
python wsb/manage.py shell
```

```python
# current Site
from django.contrib.sites.models import Site
Site.objects.filter(pk=1).update(domain='0.0.0.0', name='Local Dev')

# Add Team BIG
from csgomatches.models import Team
Team(name='BIG').save()

# Add Admin User
from django.contrib.auth.models import User
User.objects.create_superuser(username="devuser", password="devuser", email="example@example.com")
```

### 7. Run Dev Server
```shell
python wsb/manage.py runserver 0.0.0.0:9001
```
Open Browser: http://127.0.0.1:9001


