import os
import shutil
import sys
import tempfile

import pytest

BASEDIR = os.path.abspath(os.path.dirname(__file__))
PACKAGEDIR = os.path.abspath(os.path.join(BASEDIR, '..', 'src'))
sys.path.insert(0, PACKAGEDIR)

import tellsticklogger

@pytest.fixture
def csvpath():
    return BASEDIR


@pytest.fixture(scope='session', autouse=True)
def tempdir():
    tempdir = tempfile.TemporaryDirectory(dir='.')
    tellsticklogger.core.DATABASE = shutil.copy(os.path.join(BASEDIR, 'tellsticklogger.db'), tempdir.name)
    yield tempdir


@pytest.fixture
def sensors():
    return tellsticklogger.list_sensors()
