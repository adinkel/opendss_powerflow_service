from typing import List, Optional

from sqlmodel import Field, SQLModel, Relationship
from pydantic import PrivateAttr

from datetime import datetime


class BaseComponent(SQLModel):
    """
    Base circuit component
    """
    id: int | None = Field(default=None, primary_key=True)
    name: str
    _geojson_feature: bool = PrivateAttr(default=False)

class BaseEquipComponent(BaseComponent):
    """
    Base circuit equipment component which is associated with a specific circuit and geographic location
    """
    circuit: Optional[str] = Field(index=True)
    _geojson_feature: bool = PrivateAttr(default=False)

    def get_geojson_properties(self):
        ret = {}
        for attr, value in vars(self).items():
            if isinstance(value, str):
                ret[attr] = value
        return ret

class BaseLineComponent(BaseEquipComponent):
    """
    Base conduction equipment which has a starting terminal and ending terminal
    """
    _geojson_feature: bool = PrivateAttr(default=True)

    def to_geojson(self):
        coords = []
        try:
            coords.append([self.terminal1.location.x, self.terminal1.location.y])
            coords.append([self.terminal2.location.x, self.terminal2.location.y])
            geojson_properties = self.get_geojson_properties()
            return {
                "type": "Feature",
                "properties": geojson_properties,
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                }
            }
        except:
            return None

class BasePointComponent(BaseEquipComponent):
    """
    Base conducting equipment which has a single terminal and is visualized as a point on a map
    """
    _geojson_feature: bool = PrivateAttr(default=True)

    def to_geojson(self):
        try:
            coords = [self.location.x, self.location.y]
            geojson_properties = self.get_geojson_properties()
            return {
            "type": "Feature",
            "properties": geojson_properties,
            "geometry": {
                "type": "Point",
                "coordinates": coords
            }
        }
        except:
            return None

class ComponentField:
    def __init__(self, value):
        self.value = value
        self.last_updated = datetime.now()
        self.updated_by = None

    def update(self, value, user):
        self.value = value
        self.last_updated = datetime.now()
        self.updated_by = user

class Bus(BasePointComponent, table=True):
    name: Optional[str] = None
    circuit: Optional[str] = None

class Source(BasePointComponent, table=True):
    name: Optional[str] = None
    bus1: Optional[str] = None
    pu: Optional[str] = None
    basekv: Optional[float] = None
    r1: Optional[float] = None
    x1: Optional[float] = None
    r0: Optional[float] = None
    x0: Optional[float] = None
    angle: Optional[float] = None
    mvasc3: Optional[float] = None
    mvasc1: Optional[float] = None

class Switch(BasePointComponent, table=True):
    name: Optional[str] = None
    circuit: Optional[str] = None

class Cable(BasePointComponent, table=True):
    name: Optional[str] = None
    circuit: Optional[str] = None

class Capacitor(BasePointComponent, table=True):
    name: Optional[str] = None
    bus: Optional[str] = None
    kv: Optional[float] = None
    kvar: Optional[float] = None
    conn: Optional[str] = None
    phases: Optional[int] = None
    circuit: Optional[str] = None

class Generator(BasePointComponent, table=True):
    name: Optional[str] = None

class Fuse(BaseLineComponent, table=True):
    ratedCurrent: Optional[str] = None
    curve: Optional[str] = None

class WireSpacingInfo(BaseComponent, table=True):
    """
    Wire spacing data that associates multiple wire positions with the line segment, and allows to calculate line segment impedances. Number of phases can be derived from the number of associated wire positions whose phase is not neutral.
    """
    phaseCount: Optional[str] = None
    spacing: Optional[str] = None
    usage: Optional[str] = None

class WirePosition(BaseComponent, table=True):
    """
    Identification, spacing and configuration of the wires of a conductor with respect to a structure.
    """
    sequenceNumber: Optional[int] = Field(
        default=None, 
        description='Numbering for wires on a WireSpacingInfo. Neutrals should be numbered last.'
    )
    xCoord: Optional[float] = Field(default=None, description='Signed horizontal distance from the wire at this position to a common reference point.')
    yCoord: Optional[float] = Field(default=None, description='Signed vertical distance from the wire at this position: above ground (positive value) or burial depth below ground (negative value).')
    
class PerLengthSequenceImpedance(BaseComponent, table=True):
    """
    Sequence impedance parameters per unit length, for lines of 1, 2, or 3 phases
    """
    id: Optional[str] = Field(primary_key=True)
    r0: Optional[float] = Field(default=None, description='Zero sequence resistance per unit length.')
    r1: Optional[float] = Field(default=None, description='Positive sequence resistance per unit length.')
    x0: Optional[float] = Field(default=None, description='Zero sequence reactance per unit length.')
    x1: Optional[float] = Field(default=None, description='Positive sequence reactance per unit length.')
    c0: Optional[float] = Field(default=None, description='Zero sequence capacitance per unit length.')
    c1: Optional[float] = Field(default=None, description='Positive sequence capacitance per unit length.')

class WireInfo(BaseComponent, table=True):
    """
    Wire data that can be specified per line segment phase
    """
    id: Optional[str] = Field(primary_key=True, unique=True)
    sizeDescription: Optional[str] = Field(
        None,
        description='Describes the wire gauge or cross section (e.g., 4/0, #2, 336.5).',
    )
    material: Optional[str] = None
    gmr: Optional[str] = None
    radius: Optional[str] = None
    rDC20: Optional[str] = Field(
        None, description='Direct current resistance at 20 degrees celsius'
    )
    rAC: Optional[str] = None
    rAC25: Optional[str] = None
    rAC50: Optional[str] = None
    rAC75: Optional[str] = None
    ratedCurrent: Optional[str] = None
    strandCount: Optional[str] = None
    coreStrandCount: Optional[str] = None
    coreRadius: Optional[str] = None
    insulated: Optional[str] = None

class Line(BaseLineComponent, table=True):
    """
    An instance of a power line
    """
    name: Optional[str] = None
    length: Optional[float] = None
    bus1: Optional[str] = None
    bus2: Optional[str] = None
    units: Optional[str] = None
    linecode: Optional[str] = None
    switch: Optional[str] = None
    enabled: Optional[str] = None
    phases: Optional[int] = None

class LineCode(BaseComponent, table=True):
    """
    An instance of a power line
    """
    name: Optional[str] = None
    units: Optional[str] = None
    nphases: Optional[str] = None
    faultrate: Optional[str] = None
    rmatrix: Optional[str] = None
    cmatrix: Optional[str] = None
    xmatrix: Optional[str] = None
    normamps: Optional[str] = None

class Load(BasePointComponent, table=True):
    name: Optional[str] = None
    bus: Optional[str] = None
    kw: Optional[float] = None
    kvar: Optional[float] = None
    kv: Optional[float] = None
    conn: Optional[str] = None
    phases: Optional[int] = None


class Regulator(BaseLineComponent, table=True):
    name: Optional[str] = None

class Transformer(BaseLineComponent, table=True):
    name: Optional[str] = None
    bus_primary: Optional[str] = None
    bus_secondary: Optional[str] = None
    kva: Optional[float] = None
    kv_primary: Optional[float] = None
    kv_secondary: Optional[float] = None
    phases: Optional[int] = None
    circuit: Optional[str] = None

class XfmrCode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    circuit: str
    phases: Optional[int]
    windings: Optional[int]
    xhl: Optional[str]
    noloadloss: Optional[float] = Field(default=None, alias="noloadloss")
    imag: Optional[float]

class WireData(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    category: str
    name: str
    circuit: str
    normamps: Optional[float]
    diam: Optional[float]
    gmrac: Optional[float]
    rdc: Optional[float]
    rac: Optional[float]
    runits: Optional[str]
    radunits: Optional[str]
    gmrunits: Optional[str]

class LineSpacing(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    circuit: str
    nconds: Optional[int]
    nphases: Optional[int]
    units: Optional[str]
    x: Optional[str]
    h: Optional[str]

class CapControl(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    circuit: str
    capacitor: Optional[str]
    element: Optional[str]
    type: Optional[str]
    vreg: Optional[float]
    band: Optional[float]
    ptratio: Optional[float]
    ctprim: Optional[float]