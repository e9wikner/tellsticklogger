import pytest

import tellsticklogger


def test_sensor_readings(csvpath):
    timestamps, values = tellsticklogger.sensor_readings(csvpath, 226, 2, 'oregon', '1a2d')
    assert values == [79, 79, 79]


def test_list_sensors(sensors):
    sensors_id = sorted(list(set(s['id'] for s in sensors)))
    assert sensors_id == [89, 226, 240, 254]


def test_sensors_readings(csvpath):
    sensors = tellsticklogger.sensors_readings(csvpath=csvpath)
    assert 'timestamp' in sensors[0]
    assert 'values' in sensors[0]


def test_get_sensors_location_error(empty_csvpath):
    with pytest.raises(tellsticklogger.LocationNotSetError) as excinfo:
        tellsticklogger.get_sensors_location(empty_csvpath)

    assert 'not been set' in str(excinfo.value)


def test_get_sensor_location_error(csvpath):

    with pytest.raises(tellsticklogger.LocationNotSetError) as excinfo:
        tellsticklogger.get_sensor_location(181, csvpath)

    assert 'sensor 181' in str(excinfo.value)


def test_get_sensor_location(csvpath):
    location = tellsticklogger.get_sensor_location(226, csvpath)
    assert location == 'grund'


def test_set_sensor_location(sensors, csvpath):
    test_location = 'qwerty'
    sensor = {'id': 226, 'location': test_location}
    tellsticklogger.set_sensor_location(sensor, csvpath)
    assert sensor['location'] == tellsticklogger.get_sensor_location(226, csvpath)
