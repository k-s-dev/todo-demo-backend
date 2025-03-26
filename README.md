# Commands

> run commands from root of the django project

## Project setup

### Setup python env

```sh
python3 -m venv .venv
```

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

### Start project and apps

```sh
source .venv/bin/activate
django-admin startproject dj_conf .
django-admin startapp core
django-admin startapp api
```
