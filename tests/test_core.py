import pytest

import tellsticklogger


def test_sensor_readings(csvpath):
    timestamps, values = tellsticklogger.get_sensor_readings(csvpath, 180, 1, '1a2d', 'oregon')
    assert values[-1] == 50


def test_list_sensors(sensors):
    sensors_id = [s['id'] for s in sensors]
    sensors_id.sort()
    assert sensors_id == [180,]


@pytest.mark.skip
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
