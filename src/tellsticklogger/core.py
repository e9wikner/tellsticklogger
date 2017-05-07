#!usr/bin/env python
import csv
import logging, logging.config
import os
from collections import namedtuple

import asyncio
import click
from tellcore.telldus import TelldusCore, AsyncioCallbackDispatcher
from tellcore import constants

__all__ = ['constants', 'list_sensors', 'get_sensor_readings', 'set_sensor_location']

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

BASEDIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_LOGFILE = os.path.join(BASEDIR, 'logging_config.ini')
VERBOSE_LOGFILE = os.path.join(BASEDIR, 'logging_config_verbose.ini')
CSVPATH = '.'

constants.TELLSTICK_SENSOR_VALUE_TYPES = {
    1: 'TEMPERATURE',
    2: 'HUMIDITY',
    4: 'RAINRATE',
    8: 'RAINTOTAL',
    16: 'WINDDIRECTION',
    32: 'WINDAVERAGE',
    64: 'WINDGUST'}

constants.TELLSTICK_SENSOR_TYPE_VALUES = {
    'TEMPERATURE': 1,
    'HUMIDITY': 2,
    'RAINRATE': 4,
    'RAINTOTAL': 8,
    'WINDDIRECTION': 16,
    'WINDAVERAGE': 32,
    'WINDGUST': 64}


def csvfilename(id_, model, protocol, datatype):
    ''' Get filename of csv for id_'''
    datatype_str = constants.TELLSTICK_SENSOR_VALUE_TYPES[datatype]
    return '_'.join((datatype_str, protocol, model, str(id_))).lower() + '.csv'


def csvfilename_to_dict(filename):
    ''' Convert the filename back to the configuration '''
    filename = filename.rstrip('.csv')
    datatype_str, protocol, model, id_ = filename.split('_')
    return {'valuetype': datatype_str, 'protocol': protocol, 'model': model, 'id': int(id_)}


def log_sensorevent(protocol, model, id_, datatype, value, timestamp, cid):
    filename = os.path.join(CSVPATH, csvfilename(id_, model, protocol, datatype))
    with open(filename, mode='a') as f:
        to_write = '{};{}'.format(timestamp, value)
        f.writeline(to_write)
        logger.debug('{} -> {}'.format(to_write, filename))


@click.command()
@click.option('--verbose', is_flag=True, help='Increase program verbosity')
@click.option('--csvpath', help='Log to csv files here', default='.')
def cli(csvpath, verbose):
    start_logger(csvpath, verbose)


def start_logger(csvpath='.', verbose=False):
    if verbose:
        configfile = VERBOSE_LOGFILE
    else:
        configfile = DEFAULT_LOGFILE
    if not os.path.exists(configfile):
        raise OSError(configfile + ' is missing')

    logging.config.fileConfig(configfile, disable_existing_loggers=False)
    logger = logging.getLogger()

    loop = asyncio.get_event_loop()
    dispatcher = AsyncioCallbackDispatcher(loop)
    core = TelldusCore(callback_dispatcher=dispatcher)

    global CSVPATH
    CSVPATH = csvpath
    callback_id = core.register_sensor_event(log_sensorevent)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('events saved to {}'.format(csvpath))
    finally:
        core.unregister_callback(callback_id)


def get_sensor_readings(csvpath, sensor_id, valuetype, protocol, model):
    """ Return timestamps, values """

    if isinstance(valuetype, str):
        valuetype = constants.TELLSTICK_SENSOR_TYPE_VALUES[valuetype.upper()]

    filename = csvfilename(sensor_id, model, protocol, valuetype)
    with open(os.path.join(csvpath, filename)) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';')
        timestamps, values = [], []
        for row in csvreader:
            if len(row) != 2:
                logger.error('Could not read ' + ', '.join(row))
            else:
                timestamps.append(float(row[0]))
                values.append(float(row[1]))

    return timestamps, values


def list_sensors(csvpath):

    files = [f for f in os.listdir(csvpath) if f.endswith('.csv')]
    logger.info('found files: {}'.format(', '.join(files)))

    sensors = []
    for sensorfile in files:
        sensor = csvfilename_to_dict(sensorfile)
        timestamps, values = get_sensor_readings(csvpath, sensor['id'], sensor['valuetype'],
                                      sensor['protocol'], sensor['model'])
        sensor['reading'] = {timestamps[-1]: values[-1]}
        sensors.append(sensor)

    return sensors


def set_sensor_location(sensor):
    with get_database_connection() as connection:
        connection.execute("update sensors set location=:location where id=:id", sensor)
