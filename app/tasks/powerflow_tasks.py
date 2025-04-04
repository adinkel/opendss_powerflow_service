from celery import states

from opendss_powerflow_service.app.core.celery_app import app
from opendss_powerflow_service.database.engine import get_db
from opendss_powerflow_service.simulation.simulation_manager import SimulationManager
from opendss_powerflow_service.models.modelCRUD import SqlModelCRUD, SqlCircuitModelCRUD
from opendss_powerflow_service.models.result import PfResult, PfResultNode, PfResultLine

db = next(get_db())

@app.task(bind=True, send_events=True, name='tasks.powerflow.powerflow')
def run_powerflow(self, circuit_id:str, simulation_params: dict):
    self.update_state(state=states.STARTED, meta={'progress': 'file loaded'})
    modelcrud = SqlCircuitModelCRUD(db = db)
    circuit_model = modelcrud.read(circuit_id)
    simulation = SimulationManager(circuit_id, simulation_params)
    simulation.load_circuit_model(circuit_id, circuit_model)
    pf_fields = simulation.run_powerflow()
    modelcrud = SqlModelCRUD(db)
    nresults = simulation.get_node_results()
    lresults = simulation.get_line_results()
    test_result = PfResult(**pf_fields)
    modelcrud.create([test_result])
    modelcrud.update([circuit_id], nresults)
    modelcrud.update([circuit_id], lresults)
    modelcrud.db.commit()
    return {'status': 'success'}

@app.task(bind=True, send_events=True, name='tasks.powerflow.timeseries_powerflow')
def run_timeseres_powerflow(self, circuit_id:str, simulation_params: dict):
    self.update_state(state=states.STARTED, meta={'progress': 'file loaded'})
    simulation = SimulationManager(circuit_id, simulation_params)
    simulation.load_file()
    simulation.run_powerflow()
    self.update_state(state=states.SUCCESS, meta={'progress': 'timeseries powerflow run completed'})
    return {'status': 'success'}

@app.task(name='tasks.powerflow.get_powerflow_results')
def get_powerflow_results(circuit_id:str):
    modelcrud = SqlModelCRUD(db)
    nresults = modelcrud.read(PfResultNode, [circuit_id])
    lresults =  modelcrud.read(PfResultLine, [circuit_id])
    nresultslist = [i.model_dump_json() for i in nresults]
    lresultslist = [i.model_dump_json() for i in lresults]
    return {'nodes': nresultslist, 'lines': lresultslist}
