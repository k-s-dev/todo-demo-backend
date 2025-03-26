# Operations

> run commands from root of the django project

## Setup python env

```sh
python3 -m venv .venv
```

### dev

```py
import os
import pathlib as pl
import subprocess as sp

cwd = pl.Path(os.getcwd())
if not cwd.glob(".gitignore"):
    exit(1)

sp.Popen(["/bin/sh", ".venv/bin/activate"])

sp.run("python -m pip install -r requirements-base.txt", shell=True)
sp.run("python -m pip install -r requirements-dev.txt", shell=True)

sp.run("python -m pip freeze > requirements.txt", shell=True)
```

### prod

```py
import os
import pathlib as pl
import subprocess as sp

cwd = pl.Path(os.getcwd())
if not cwd.glob(".gitignore"):
    exit(1)

sp.Popen(["/bin/sh", ".venv/bin/activate"])

sp.run("python -m pip install -r requirements-base.txt", shell=True)

sp.run("python -m pip freeze > requirements.txt", shell=True)
```

## Project setup

### Start project and apps

```sh
source .venv/bin/activate
django-admin startproject dj_conf .
django-admin startapp core
django-admin startapp api
```

### Setup environments

```sh
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```sh
# .env
SECRET_KEY="generated key"
```

```sh
# .env.dev
DEBUG=True
ALLOWED_HOSTS="*"
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
```

```sh
# .env.prod
DEBUG=False
ALLOWED_HOSTS="*"
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
```

### Configure project settings

- settings are split across 3 files: base, dev and prod

## Database

### Setup core models

- setup models and register with admin
- fixtures for initial data

- to prepare fixtures after models are setup and some data added
  using admin page
  - make admin user


```sh
./manage.py createsuperuser
```

```sh
./manage.py dumpdata auth > ./core/fixtures/core/admin.json
./manage.py dumpdata core > ./core/fixtures/core/sample-data.json
```

### Prepare db

- initial load

```sh
./manage.py makemigrations && ./manage.py migrate
./manage.py loaddata core/admin.json core/sample-data.json
```

## Run server

### dev

```sh
./manage.py runserver --settings=dj_conf.settings.dev
```

### prod

```sh
./manage.py runserver --settings=dj_conf.settings.prod
```

