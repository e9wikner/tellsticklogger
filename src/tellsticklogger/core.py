#!usr/bin/env python
import atexit
import logging, logging.config
import os
import sqlite3

import asyncio
import click
from tellcore.telldus import TelldusCore, AsyncioCallbackDispatcher
from tellcore import constants

__all__ = ['constants', 'DATABASE', 'list_sensors', 'get_last_sensor_reading', 'set_sensor_location']

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

BASEDIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_LOGFILE = os.path.join(BASEDIR, 'logging_config.ini')
VERBOSE_LOGFILE = os.path.join(BASEDIR, 'logging_config_verbose.ini')

constants.TELLSTICK_SENSOR_VALUE_TYPES = {
    1: 'TEMPERATURE',
    2: 'HUMIDITY',
    4: 'RAINRATE',
    8: 'RAINTOTAL',
    16: 'WINDDIRECTION',
    32: 'WINDAVERAGE',
    64: 'WINDGUST'}

DATABASE = os.path.join(BASEDIR, 'tellsticklogger.db')
database_connection = None


def get_database_connection():
    """ Opens up a connection to the tellsticklogger database.
    """
    global database_connection

    if database_connection is None:
        logger.debug('connecting to {}'.format(DATABASE))
        database_connection = sqlite3.connect(DATABASE)
        database_connection.row_factory = sqlite3.Row  # To access columns by name instead of index
        atexit.register(close_database_connection)

    return database_connection


def close_database_connection():
    if database_connection is not None:
        database_connection.close()
        logger.debug('{} connection closed'.format(DATABASE))


def init_db(sensors):

    connection = get_database_connection()

    with connection:
        currenttables = set(row[0] for row in connection.execute(
            "select name from sqlite_master where type='table'").fetchall())

        sensors = set(sensors)
        sensortables = set('sensor_{}'.format(sensor.id) for sensor in sensors)

        if 'sensors' not in currenttables:
            connection.execute('create table sensors (id integer unique,  '
                               'protocol text, model text, type integer)')
            logger.info("created table sensors")

        sensorids_current = set(row[0] for row in connection.execute(
            "select id from sensors").fetchall())
        logger.info('Current sensors: {}'.format(sensorids_current))

        for s in sensors:
            if s.id not in sensorids_current:
                connection.execute("insert into 'sensors' values (?,?,?,?)",
                                      (s.id, s.protocol, s.model, s.datatypes))
                logger.info('added {} to sensors'.format(s.id))

        for table in sensortables - currenttables:
            connection.execute('create table {} '.format(table) +
                                  '(timestamp integer, value real, type integer)')
            logger.info("created table " + table)


def sensor_event_to_database(protocol, model, id_, datatype, value, timestamp, cid):

    table = 'sensor_{}'.format(id_)
    with get_database_connection() as connection:
        connection.execute(
            'insert into ' + table + ' (timestamp, value, type) values (?,?,?)',
            (timestamp, value, datatype))
        logger.debug('({},{},{}) -> {}'.format(timestamp, value, datatype, table))


@click.command()
@click.option('--verbose', is_flag=True, help='Increase program verbosity')
@click.argument('sqlite3_path')
def cli(sqlite3_path, verbose):
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

    init_db(database=os.path.abspath(sqlite3_path), sensors=core.sensors())
    callback_id = core.register_sensor_event(sensor_event_to_database)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('events saved to {}'.format(sqlite3_path))
    finally:
        core.unregister_callback(callback_id)


def get_last_sensor_reading(sensor_id, valuetype):
    with get_database_connection() as connection:
        lastrow = connection.execute(
            "select * from sensor_{} where type=? order by timestamp desc limit 1"
            .format(sensor_id), str(valuetype)).fetchall()[-1]

    return {lastrow['timestamp']: lastrow['value']}


def list_sensors():

    with get_database_connection() as connection:
        sensors_rows = connection.execute("select * from sensors").fetchall()
    logger.info('fetched {} sensors from sensors table'.format(len(sensors_rows)))

    sensors = [dict(row) for row in sensors_rows]
    for sensor in sensors:

        value_types = {k: constants.TELLSTICK_SENSOR_VALUE_TYPES[k]
                       for k in constants.TELLSTICK_SENSOR_VALUE_TYPES
                       if k & sensor['type']}

        last_reading = {}
        for valuetype_int, valuetype_str in value_types.items():
            try:
                reading = get_last_sensor_reading(sensor['id'], valuetype_int)
            except IndexError:
                reading = None
            last_reading[valuetype_str] = reading

        sensor['reading'] = last_reading
        sensor['type'] = list(value_types.values())

    return sensors


def set_sensor_location(sensor):
    with get_database_connection() as connection:
        connection.execute("update sensors set location=:location where id=:id", sensor)
