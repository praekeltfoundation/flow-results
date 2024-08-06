FROM ghcr.io/praekeltfoundation/docker-django-bootstrap-nw:py3.9-bullseye

COPY . /app
RUN pip install -e .

RUN DJANGO_SETTINGS_MODULE=flow_results.testsettings python manage.py collectstatic --noinput
ENV DJANGO_SETTINGS_MODULE=flow_results.settings
ENV DEBUG=false

CMD [\
    "flow_results.wsgi:application",\
    "--workers=2",\
    "--threads=4",\
    "--worker-class=gthread",\
    "--worker-tmp-dir=/dev/shm"\
]
