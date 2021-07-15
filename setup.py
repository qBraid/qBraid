from setuptools import setup, find_packages

with open("qbraid/_version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")

setup(
    name="qbraid",
    version=version,
    description="Platform for accessing quantum computers",
    url="https://github.com/qBraid/qBraid",
    author="qBraid Development Team",
    author_email="noreply@qBraid.com",
    license="Restricted",
    packages=find_packages(exclude=["test*"]),
    zip_safe=False,
)
