from setuptools import setup

with open("qbraid/_version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")

setup(version=version)
