# Flow Results

An implementation of the [flow results API](https://floip.gitbook.io/flow-results-specification/)

## Usage
Have a look at the [API specification documentation](https://floip.gitbook.io/flow-results-specification/api-specification) for documentation of the API endpoints.

Users, authentication tokens, and permissions can be managed through the django admin page, available at `/admin/`. To create the first admin user, run `python manage.py createsuperuser`.

## Running in Production
There is a [docker image](https://hub.docker.com/r/praekeltfoundation/flow-results) that can be used to easily run this service. It uses the following environment variables for configuration:

| Variable      | Description |
| ----------    | ----------- |
| SECRET_KEY    | The django secret key, set to a long, random sequence of characters |
| DATABASE_URL  | Where to find the database. Set to `sqlite:////path/to/volume/db.sqlite` for a mounted volume sqlite database, or `postgresql://host:port/db` for a postgresql database |
| ALLOWED_HOSTS | Comma separated list of hostnames for this service, eg. `host1.example.org,host2.example.org` |

[See also this README](https://github.com/praekeltfoundation/docker-django-bootstrap#configuring-gunicorn) for more configuration options for tuning the config

## Development
Requires Python 3.6 or greater

Install dependencies:
```bash
pip install -e .[dev]
```

Auto format and run tests:
```bash
./format_and_test.sh
```

Run dev server:
```bash
python manage.py migrate
python manage.py runserver
```
