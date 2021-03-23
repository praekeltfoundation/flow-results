set -e

black .
isort .
flake8 .
coverage run manage.py test
coverage report
