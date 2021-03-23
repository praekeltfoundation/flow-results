FROM praekeltfoundation/django-bootstrap:py3.7-stretch

COPY . /app
RUN pip install -e .

RUN python manage.py collectstatic --noinput
ENV DJANGO_SETTINGS_MODULE flow_results.settings
ENV DEBUG false

CMD ["flow_results.wsgi:application"]
