import datetime

from pydantic import TypeAdapter
from typing import List
from sqlmodel import select, delete
from sqlalchemy.sql import text
from sqlalchemy.exc import NoResultFound, IntegrityError
from psycopg2.errors import UniqueViolation

from opendss_powerflow_service.models.circuit import Circuit, Circuits
from opendss_powerflow_service.models.components import Transformer, Line, LineCode, Capacitor, Bus, Source, Load


class SqlModelCRUD:
    """
    CRUD operations for a list of SQLModel objects
    """

    def __init__(self, db):
        self.db = db

    def create(self, sql_model):
        for sql_table_model in sql_model:
            self.db.add(sql_table_model)

    def read(self, sql_model, circuit_ids=None):
        adapter = TypeAdapter(sql_model)
        result = []
        if circuit_ids is None:
            statement = select(sql_model)
            rows = self.db.execute(statement).all()
        else:
            rows = self.db.execute(select(sql_model).where(sql_model.circuit.in_(circuit_ids))).all()
        for row in rows:
            for item in row:
                result.append(adapter.validate_python(item))
        return result

    def update(self, circuit_ids, sql_table_models):
        self.delete(circuit_ids, sql_table_models)
        for sql_table_model in sql_table_models:
            self.db.add(sql_table_model)

    def delete(self, circuit_ids:str, sql_table_models):
        if sql_table_models:
            m = sql_table_models[0]
            if hasattr(m, '__tablename__'):
                
                statement = text("DELETE FROM " + m.__tablename__ + " WHERE circuit IN ('" + "','".join(circuit_ids) + "')")
            self.db.execute(statement)

        
class SqlCircuitModelCRUD:
    """
    CRUD operations for a Circuit model
    """

    def __init__(self, db):
        self.db = db

    def create(self, circuit_model, circuit_id):
        try:
            circuit_model.fields.CircuitId = circuit_id
            circuit_model.fields.LastUpdated = str(datetime.datetime.now())
            self.db.add(circuit_model.fields)
            for component in circuit_model:
                self.db.add(component)
        except IntegrityError as e:
            if isinstance(e.orig, UniqueViolation):
                raise Exception('Circuit already exists')
            else:
                raise e
            
    def _read_model(self, model, circuit_id):
        ret = []
        rows = self.db.execute(select(model).where(model.circuit == circuit_id)).all()
        for row in rows:
            for item in row:
                if item:
                    ret.append(item)
        return ret
    
    def _read_equip(self, model):
        ret = []
        rows = self.db.execute(select(model)).all()
        for row in rows:
            for item in row:
                if item:
                    ret.append(item)
        return ret
    
    def read(self, circuit_id):
        try:
            statement = select(Circuits).where(Circuits.circuit == circuit_id)
            circuit_info_rows = self.db.execute(statement).one()
            Circuitss = TypeAdapter(List[Circuits]).validate_python(circuit_info_rows)
            circuit_model = Circuit(fields=Circuitss[0])
            circuit_model.linecodes = self._read_equip(LineCode)
            circuit_model.sources = self._read_model(Source, circuit_id)
            circuit_model.transformers = self._read_model(Transformer, circuit_id)
            circuit_model.capacitors = self._read_model(Capacitor, circuit_id)
            circuit_model.lines = self._read_model(Line, circuit_id)
            circuit_model.buses = self._read_model(Bus, circuit_id)
            circuit_model.loads = self._read_model(Load, circuit_id)
            return circuit_model
        except NoResultFound as e:
            raise Exception('Circuit not found')
        except Exception as e:
            raise Exception(e)

    def update(self, circuit_model:Circuit, circuit_id:str):
        self.delete(circuit_model, circuit_id)
        circuit_model.fields.CircuitId = circuit_id
        circuit_model.fields.LastUpdated = str(datetime.datetime.now())
        self.db.add(circuit_model.fields)
        for component in circuit_model.get_components_w_attribute('circuit'):
            self.db.add(component)
        
    def delete(self, circuit_model, circuit_id:str):
        self.db.execute(delete(Circuits).where(Circuits.CircuitId == circuit_id))
        models_f = circuit_model.get_models_w_attrib('circuit')
        for model in models_f:
            result = self.db.execute(delete(model).where(model.circuit == circuit_id))

        
