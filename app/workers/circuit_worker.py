from opendss_powerflow_service.app.core.celery_app import app
from opendss_powerflow_service.app.tasks.circuit_tasks import create_circuit, update_circuit, read_circuit, get_circuits


def start_worker():
    # logic to start the Celery worker
    app.worker_main(['-A', 'opendss_powerflow_service.app.core.celery_app', 'worker', '--loglevel=INFO', '-Q', 'circuit_queue', '-n', 'circuit_worker@%h', '--pool=solo'])

if __name__ == '__main__':
    start_worker()