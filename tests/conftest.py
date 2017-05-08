import logging
import os
import shutil
import sys

import pytest

logging.basicConfig(level=logging.DEBUG)

BASEDIR = os.path.abspath(os.path.dirname(__file__))
PACKAGEDIR = os.path.abspath(os.path.join(BASEDIR, '..', 'src'))
sys.path.insert(0, PACKAGEDIR)

import tellsticklogger

@pytest.fixture
def csvpath(tmpdir):
    dst = os.path.join(tmpdir.strpath, 'fixtures')
    shutil.copytree(os.path.join(BASEDIR, 'fixtures'), dst)
    return dst


@pytest.fixture
def empty_csvpath(csvpath):
    p = os.path.join(csvpath, 'emptydir')
    os.makedirs(p)
    return p


@pytest.fixture
def sensors(csvpath):
    return tellsticklogger.sensors(csvpath=csvpath, include_all_readings=True)


@pytest.fixture
def sensors_lastreading(csvpath):
    return tellsticklogger.sensors(csvpath=csvpath)
