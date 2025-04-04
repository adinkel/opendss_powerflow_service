import logging
from sqlmodel import SQLModel

from opendss_powerflow_service.database.engine import engine

from opendss_powerflow_service.models.circuit import Circuit, Circuits
from opendss_powerflow_service.models.components import Bus, Transformer, Capacitor, Line, Load
from opendss_powerflow_service.models.result import PfResult, PfResultNode, PfResultLine
from opendss_powerflow_service.models.params import SimulationParams


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_tables(engine):
    SQLModel.metadata.drop_all(engine)

def init_db(engine):
    SQLModel.metadata.create_all(engine)

def init() -> None:
    drop_tables(engine)
    init_db(engine)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()