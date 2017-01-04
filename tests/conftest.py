import os
import shutil
import tempfile

import pytest

import tellsticklogger

BASEDIR = os.path.abspath(os.path.dirname(__file__))

@pytest.fixture(scope='session', autouse=True)
def tempdir():
    tempdir = tempfile.TemporaryDirectory(dir='.')
    tellsticklogger.core.DATABASE = shutil.copy(os.path.join(BASEDIR, 'tellsticklogger.db'), tempdir.name)
    yield tempdir


@pytest.fixture
def sensors():
    return tellsticklogger.list_sensors()
