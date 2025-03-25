import os
import pathlib as pl
import subprocess as sp

cwd = pl.Path(os.getcwd())
if not cwd.glob(".gitignore"):
    exit(1)

sp.run("source .venv/bin/python", shell=True)
sp.run("python -m pip install -r requirements-base.txt", shell=True)
sp.run("python -m pip freeze > requirements.txt", shell=True)

