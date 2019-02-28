**Resolwe server for Orange data mining**


Install requirements:

```bash
pip install -r requirements.txt
```

Start PostgreSQL, Redis, and Elasticsearch Docker containers:

```bash
docker-compose up
```

Setup project database:

```bash
python manage.py migrate
python manage.py createsuperuser --username admin --email admin@example.com
python manage.py register
python manage.py elastic_index
python manage.py elastic_mapping
```

Run servers (each in a separate terminal window):

```bash
python manage.py runserver # Django development server
python manage.py runworker rest_framework_reactive.worker rest_framework_reactive.poll_observer rest_framework_reactive.throttle resolwe-server.manager.control flow.purge
python manage.py runlistener # Executor listener server
celery -A resolwe_server worker --queues=ordinary,hipri --loglevel=info # Celery workload manager
```
