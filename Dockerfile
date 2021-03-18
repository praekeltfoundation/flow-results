FROM praekeltfoundation/django-bootstrap:py3.7-stretch

COPY . /app
RUN pip install -e .

ENV DJANGO_SETTINGS_MODULE flow_results.settings
ENV DEBUG false
RUN SECRET_KEY=placeholder python manage.py collectstatic --noinput

CMD ["flow_results.wsgi:application"]