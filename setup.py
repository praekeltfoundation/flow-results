from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="flow_results",
    version="0.0.1",
    packages=find_packages(),
    url="https://github.com/praekeltfoundation/flow-results",
    license="BSD 3-Clause License",
    author="Praekelt.org",
    author_email="dev@praekelt.org",
    description="Implementation of the flow results API "
    "https://floip.gitbook.io/flow-results-specification/",
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={
        "Bug Tracker": "https://github.com/praekeltfoundation/flow-results/issues",
        "Documentation": "https://floip.gitbook.io/flow-results-specification/",
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Django :: 4.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    install_requires=[
        "django==4.2.16",
        "django-environ==0.4.5",
        "djangorestframework==3.15.2",
        "drf-extensions==0.7.0",
        "django-health-check==3.18.3",
        "django-prometheus==2.3.1",
        "psycopg2-binary==2.9.9",
        "sentry-sdk==2.8.0",
        "dj-database-url==2.2.0",
        "python-dateutil==2.8.2",
        "setuptools==72.1.0",
    ],
    extras_require={
        "dev": [
            "black==22.10.0",
            "isort==5.7.0",
            "flake8==7.1.1",
            "coverage==5.5",
        ],
    },
)
