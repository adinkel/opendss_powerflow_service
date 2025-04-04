from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional


class Difference(BaseModel):
    object: str
    attribute: str
    value: str

class DifferenceModel(BaseModel):
    forward: List[Difference] = [{'object': 'transformer', 'attribute': 'name', 'value': 'new name'}]
    reverse: List[Difference] = [{'object': 'transformer', 'attribute': 'name', 'value': 'old name'}]

class SimulationOutputs(str, Enum):
    voltage = "voltage"
    current = "current"
    violations = "violations"

class ModelCreationParams(BaseModel):
    initial_state: dict = Field(
        default={"capacitors_initially_on" : "True"}, description='Model Setup and creation parameters')
    difference_model: DifferenceModel

class SimulationParamsTimeSeries(BaseModel):
    starttime: Optional[str] = "2009-07-21 00:00:00"
    endtime: Optional[str] = "2009-07-21 00:00:00"
    timestep: Optional[int] = 60
    modelpath: Optional[str] = None
    setup: ModelCreationParams
    outputs: Optional[List[SimulationOutputs]] = Field(
        default=["voltage", "current", "violations"], description='')
    
class SimulationParams(BaseModel):
    outputs: Optional[List[SimulationOutputs]] = Field(
        default=["voltage", "current", "violations"], description='')
    