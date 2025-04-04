## Overview

API and distributed task queue for OpenDSS

## Dependencies

* <a href="https://github.com/fastapi/fastapi" target="_blank"><code>fastapi</code></a> for api and docs
* <a href="https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html" target="_blank"><code>celery</code></a> distributed task queue

## Usage (running locally):

Add database connection info to `app.database.settings`

Start rabbitmq message broker (if the management plug-in is enabled: http://localhost:15672/):

 ```console
$ rabbitmqctl start_app
```

Start a celery workers:
 ```console
$ python -m opendss_powerflow_service.app.workers.powerflow_worker
$ python -m opendss_powerflow_service.app.workers.circuit_worker
```

Celery Flower if applicable (http://localhost:5555/)

 ```console
$ celery -A opendss_powerflow_service.app.core.celery_app --broker=amqp://guest:guest@localhost:5672/myvhost flower
```

FastAPI (http://127.0.0.1:8000/docs)
python -m fastapi dev .\opendss_powerflow_service\app\main.py

```console
$ fastapi dev app\main.py
```

![Alt text](images/screenshot.png)


