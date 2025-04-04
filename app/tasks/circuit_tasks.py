import json

from sqlalchemy.exc import IntegrityError

from opendss_powerflow_service.utils.log import get_logger
from opendss_powerflow_service.database.engine import get_db
from opendss_powerflow_service.app.core.celery_app import app

from opendss_powerflow_service.models.circuit import Circuit as CircuitDBModel
from opendss_powerflow_service.models.circuit import Circuits

from opendss_powerflow_service.models.modelCRUD import SqlModelCRUD, SqlCircuitModelCRUD

db_session = next(get_db())

logger = get_logger('circuit_tasks')

def _commit(db_session):
    try:
        db_session.commit()  
    except IntegrityError as e:
            raise Exception('Circuit already exists')
    except Exception as e:
         raise Exception(e)  

def _serialize(model):
    if hasattr(model, 'model_dump'):
        return model.model_dump()
    else:
        return model

@app.task(name='tasks.circuit.get_circuits')
def get_circuits():
    reader = SqlModelCRUD(db = db_session)
    circuit_list = reader.read(Circuits)
    circuit_list_serializable = []
    for row in circuit_list:
        circuit_list_serializable.append([_serialize(i) for i in row])
    return json.dumps({"circuit_list": circuit_list_serializable}, indent=4, default=str)

@app.task(name='tasks.circuit.create')
def create_circuit(circuit_id, circuit_data):
    circuit_model = CircuitDBModel()
    circuit_model.from_json(circuit_data)
    modelcrud = SqlCircuitModelCRUD(db = db_session)
    circuit_model = modelcrud.create(circuit_model, circuit_id)
    _commit(modelcrud.db)
    return {"message": "Circuit Created"}

@app.task(name='tasks.circuit.read')
def read_circuit(circuit_id):
    circuit_model = CircuitDBModel()
    modelcrud = SqlCircuitModelCRUD(db = db_session)
    circuit_model = modelcrud.read(circuit_id)
    return {"circuit_model": circuit_model.model_dump_json()}

@app.task(name='tasks.circuit.update')
def update_circuit(circuit_id, circuit_data):
    circuit_model = CircuitDBModel()
    circuit_model.from_json(circuit_data)
    modelcrud = SqlCircuitModelCRUD(db = db_session)
    circuit_model = modelcrud.update(circuit_model, circuit_id)
    modelcrud.db.commit()
    return {"message": "Circuit Updated"}

@app.task(name='tasks.circuit.delete')
def delete_circuit(circuit_id):
    circuit_model = CircuitDBModel()
    modelcrud = SqlCircuitModelCRUD(db = db_session)
    circuit_model = modelcrud.delete(circuit_model, circuit_id)
    modelcrud.db.commit()
    return {"message": "Circuit Deleted"}