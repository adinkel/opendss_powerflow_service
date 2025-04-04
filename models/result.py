from typing import Optional
from sqlmodel import Field, SQLModel

class PfResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    circuit: Optional[str] = None
    run_timestamp: Optional[str] = None
    converged: Optional[str] = None
    mode: Optional[str] = None
    process_time:  Optional[str] = None
    total_time:  Optional[str] = None
    total_iterations:  Optional[str] = None
    control_iterations: Optional[str] = None
    algorithm: Optional[str] = None
    control_mode: Optional[str] = None
    convergence: Optional[str] = None

class PfResultNode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: Optional[str] = None
    circuit: Optional[str] = Field(index=True)
    volta: Optional[float] = None
    voltb: Optional[float] = None
    voltc: Optional[float] = None
    nominal_voltage: Optional[float] = None
    pu_voltage: Optional[float] = None

class PfResultLine(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: Optional[str] = None
    circuit: Optional[str] = Field(index=True)
    imax: Optional[float] = None
    kw: Optional[float] = None
    kvar: Optional[float] = None
    kva: Optional[float] = None
    pf: Optional[float] = None
    loading_percent: Optional[float] = None
    normal_rating: Optional[float] = None
    emergency_rating: Optional[float] = None