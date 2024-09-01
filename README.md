# Contribution
Feel free to hack around and create pull requests.

## Developement

### 1. Create and activate Python 3.6 or greater virtual environment
```shell
python3 -m venv wannspieltbig_dev
cd wannspieltbig_dev
source bin/activate
```

### 2. Install requirements
```shell
mkdir src
cd src
git clone https://github.com/ckarrie/ckw-csgo/
pip install -r ckw-csgo/requirements.txt
# install csgo app in editable mode
pip install -e ckw-csgo
```

### 3. Set up local Django project
```shell
django-admin startproject wsb
cd wsb/
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
from csgomatches.models import Team
Team(name='BIG').save()

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
