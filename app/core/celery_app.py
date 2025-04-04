from opendss_powerflow_service.app.config.config import settings

from celery import Celery
from kombu import Queue


# Initialize Celery
app = Celery(
    'app', 
    broker = 'pyamqp://myuser:mypassword@localhost:5672/myvhost', 
    backend= 'db+postgresql://postgres:mypassword@localhost:5432/postgres'
    )

app.conf.task_default_queue = 'default'

## Using the database to store task state and results.
result_persistent = True

app.conf.task_queues = (
    Queue('default'),
    Queue('circuit_queue'),
    Queue('powerflow_queue')
)

# Celery configurations
app.conf.task_routes = {
    'tasks.circuit.*': {'queue': 'circuit_queue'},
    'tasks.powerflow.*': {'queue': 'powerflow_queue'}
}

# List of modules to import when the Celery worker starts.
imports = ('opendss_powerflow_service.app.tasks.circuit_tasks', 'opendss_powerflow_service.app.tasks.circuit_tasks')