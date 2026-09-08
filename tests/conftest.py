import ee
from pfh.scripts.config import EE_PROJECT


def pytest_sessionstart(session):
    ee.Initialize(project=EE_PROJECT)
