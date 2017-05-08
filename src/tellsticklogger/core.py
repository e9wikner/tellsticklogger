#!usr/bin/env python
import csv
import json
import logging, logging.config
import os
from collections import namedtuple

import asyncio
import click
from tellcore.telldus import TelldusCore, AsyncioCallbackDispatcher
from tellcore import constants

__all__ = ['constants', 'sensors', 'sensor_readings',
           'get_sensor_location', 'get_sensors_location', 'set_sensor_location', 'LocationNotSetError']

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


class CouldNotParseFilename(Exception):
    pass


class LocationNotSetError(Exception):
    pass


def csvfilename(id_, model, protocol, datatype):
    ''' Get filename of csv for id_'''
    datatype_str = constants.TELLSTICK_SENSOR_VALUE_TYPES[datatype]
    return '_'.join((datatype_str, protocol, model, str(id_))).lower() + '.csv'


def csvfilename_to_dict(filename):
    ''' Convert the filename back to the configuration '''
    filename = filename.rstrip('.csv')
    datatype_str, protocol, model, id_ = filename.split('_')
    try:
        return {'valuetype': datatype_str, 'protocol': protocol, 'model': model, 'id': int(id_)}
    except ValueError:
        raise CouldNotParseFilename(filename + '.csv')


def log_sensorevent(protocol, model, id_, datatype, value, timestamp, cid):
    filename = os.path.join(CSVPATH, csvfilename(id_, model, protocol, datatype))
    with open(filename, mode='a') as f:
        to_write = '{};{}'.format(timestamp, value)
        f.write(to_write + '\n')
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
        logger.info('waiting for event')
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('events saved to {}'.format(csvpath))
    finally:
        core.unregister_callback(callback_id)


def sensor_readings(sensor_id, valuetype, protocol, model, csvpath='.'):
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
                timestamps.append(int(row[0]))
                values.append(float(row[1]))

    return timestamps, values


def sensor_locationfile(csvpath='.'):
    locationfile = os.path.join(csvpath, 'locations.json')
    logger.debug('locationfile: ' + locationfile)
    return locationfile


def get_sensors_location(csvpath='.'):
    try:
        with open(sensor_locationfile(csvpath)) as fileobject:
            locations = json.load(fileobject)
    except FileNotFoundError:
        raise LocationNotSetError('Locations has not been set yet.')
    else:
        return locations

def get_sensor_location(sensor_id, csvpath='.'):
    sensor_id = str(sensor_id)  # Just in case an int was given
    locations = get_sensors_location(csvpath=csvpath)
    if sensor_id not in locations:
        raise LocationNotSetError('No location for sensor {} is set'.format(sensor_id))

    return locations[sensor_id]


def set_sensor_location(sensordict, csvpath='.'):
    locationfile = sensor_locationfile(csvpath=csvpath)
    if not os.path.isfile(locationfile):
        logger.debug('creating location file ' + locationfile)
        locations = {}
    else:
        with open(sensor_locationfile(csvpath=csvpath), mode='r') as fileobject:
            locations = json.load(fileobject)

    locations[sensordict['id']] = sensordict['location']
    with open(sensor_locationfile(csvpath=csvpath), mode='w') as fileobject:
        json.dump(locations, fileobject)


def sensors(csvpath='.', include_all_readings=False):

    files = [f for f in os.listdir(csvpath) if f.endswith('.csv')]
    logger.info('found files: {}'.format(', '.join(files)))

    sensorss = []
    for sensorfile in files:
        try:
            sensor = csvfilename_to_dict(sensorfile)
        except CouldNotParseFilename as err:
            logger.debug('not a sensorfile: ' + str(err))
            continue

        timestamps, values = sensor_readings(
                sensor['id'], sensor['valuetype'], sensor['protocol'], sensor['model'],
                csvpath=csvpath)

        sensor['reading'] = {timestamps[-1]: values[-1]}
        if include_all_readings:
            sensor['timestamps'], sensor['values'] = timestamps, values

        try:
            sensor['location'] = get_sensor_location(sensor['id'], csvpath=csvpath)
        except LocationNotSetError:
            pass
        sensorss.append(sensor)

    return sensorss
