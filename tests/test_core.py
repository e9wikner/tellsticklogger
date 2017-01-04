import os
import sqlite3

import tellsticklogger


def test_database_connection():
    assert os.path.exists(tellsticklogger.core.DATABASE)
    connection = tellsticklogger.core.get_database_connection()
    assert isinstance(connection, sqlite3.Connection)


def test_last_sensor_reading():
    reading = tellsticklogger.get_last_sensor_reading(248, 1)
    timestamp = list(reading.keys())[0]
    value = reading[timestamp]
    assert value == '4.8'


def test_list_sensors(sensors):
    sensors_id = [s['id'] for s in sensors]
    sensors_id.sort()
    assert sensors_id == [135, 180, 226, 248]


def test_set_sensor_location(sensors):
    sensor = sensors[0]
    current_location = sensor['location']
    sensor_id = sensor['id']

    test_location = 'qwerty'
    sensor['location'] = test_location
    tellsticklogger.set_sensor_location(sensor)

    sensor = [s for s in tellsticklogger.list_sensors()
              if s['id'] == sensor_id][0]

    assert sensor['location'] == test_location
