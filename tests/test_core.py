import pytest

import tellsticklogger


def test_sensor_readings(csvpath):
    timestamps, values = tellsticklogger.get_sensor_readings(csvpath, 226, 2, 'oregon', '1a2d')
    assert values == [79, 79, 79]


def test_list_sensors(sensors):
    sensors_id = sorted(list(set(s['id'] for s in sensors)))
    assert sensors_id == [89, 226, 240, 254]


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
