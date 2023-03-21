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
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Django :: 3.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    install_requires=[
        "django==3.2.18",
        "django-environ==0.4.5",
        "djangorestframework==3.12.2",
        "drf-extensions==0.7.0",
        "django-health-check==3.16.3",
        "django-prometheus==2.1.0",
        "psycopg2-binary==2.8.6",
        "sentry-sdk==1.14.0",
    ],
    extras_require={
        "dev": [
            "black==22.10.0",
            "isort==5.7.0",
            "flake8==5.0.4",
            "coverage==5.5",
        ],
    },
)
