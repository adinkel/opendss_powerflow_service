from opendss_powerflow_service.app.core.celery_app import app
from opendss_powerflow_service.app.tasks.powerflow_tasks import run_powerflow, run_timeseres_powerflow, get_powerflow_results


def start_worker():
    # logic to start the Celery worker
    app.worker_main(['-A', 'opendss_powerflow_service.app.core.celery_app','worker', '--loglevel=INFO', '-Q', 'default,powerflow_queue', '-n', 'powerflow_worker@%h', '-E', '--pool=threads', '--concurrency=1'])


if __name__ == '__main__':
    start_worker()