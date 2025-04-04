from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from celery.result import AsyncResult

from opendss_powerflow_service.app.core.celery_app import app as celery_app
from opendss_powerflow_service.utils.log import get_logger
from opendss_powerflow_service.database.engine import get_db
from opendss_powerflow_service.app.tasks import circuit_tasks, powerflow_tasks
from opendss_powerflow_service.models.params import SimulationParams

router = APIRouter()
logger = get_logger('api_routes')

@router.get("/circuit/", tags=["Circuit"])
def get_circuits_list(db: Session = Depends(get_db)):
    circuit_list = circuit_tasks.get_circuits()
    return {"circuit_list": circuit_list}

@router.get("/circuit/{circuit_id}", tags=["Circuit"])
def get_circuit(circuit_id: str, db: Session = Depends(get_db)):
    circuit_model = circuit_tasks.read_circuit(circuit_id)
    if circuit_model is None:
        raise HTTPException(status_code=404, detail="Circuit not found")
    return circuit_model

@router.post("/circuit/{circuit_id}", tags=["Circuit"])
def create_circuit(circuit_id: str, circuit_data: dict, db: Session = Depends(get_db)):
    message = circuit_tasks.create_circuit.delay(circuit_id, circuit_data)
    return message

@router.put("/circuit/{circuit_id}", tags=["Circuit"])
def update_circuit(circuit_id: str, circuit_data: dict, db: Session = Depends(get_db)):
    result = circuit_tasks.update_circuit.delay(circuit_id, circuit_data)
    return {"message": "Circuit Updated Initiated", "result": result}
    
@router.post("/powerflow/{circuit_id}", tags=["Powerflow"])
def powerflow(circuit_id: str, simulation_params: SimulationParams, db:Session = Depends(get_db)):
    task = powerflow_tasks.run_powerflow.delay(circuit_id, simulation_params.model_dump_json())
    return {"task_id": str(task.id)}

@router.post("/powerflow/timeseres_powerflow/{circuit_id}", tags=["Powerflow"])
def run_timeseres_powerflow(circuit_id: str, simulation_params: dict, db:Session = Depends(get_db)):
    task = powerflow_tasks.run_powerflow.delay(circuit_id, simulation_params)
    return {"task_id": str(task.id)}

@router.get("/powerflow/status/{task_id}", tags=["Powerflow"])
async def get_status(task_id: str, db:Session = Depends(get_db)):
    result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": result.status, "result": result.result}

@router.get("/powerflow/result/{circuit_id}", tags=["Powerflow"])
def get_powerflow_results(circuit_id: str, db:Session = Depends(get_db)):
    results = powerflow_tasks.get_powerflow_results(circuit_id)
    return results