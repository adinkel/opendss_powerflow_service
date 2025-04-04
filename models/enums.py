from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Material(Enum):
    copper = 'copper'
    steel = 'steel'
    alumnimum = 'alumnimum'
    acsr = 'acsr'
    aluminumAlloy = 'aluminumAlloy'
    aaac = 'aaac'

class Usage(Enum):
    transmission = 'transmission'
    distribution = 'distribution'
    secondary = 'secondary'
    service = 'service'

class PhaseCode(Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    N = 'N'
    s1 = 's1'
    s2 = 's2'
    s12 = 's12'
    ABC = 'ABC'
    ABN = 'ABN'
    ACN = 'ACN'
    BCN = 'BCN'
    ABCN = 'ABCN'
    s12N = 's12N'