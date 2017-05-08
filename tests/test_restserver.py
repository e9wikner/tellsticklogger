from flask import json
import pytest

import tellsticklogger.restserver


URI_TELLSTICK_API = '/tellsticklogger/api'

@pytest.fixture
def app(csvpath):
    app = tellsticklogger.restserver.app
    app.config['TESTING'] = True
    app.config['CSVPATH'] = csvpath
    return app


@pytest.fixture(params=['v0.1',])
def sensors_uri(request):
    return '/'.join((URI_TELLSTICK_API, request.param, 'sensors'))

def test_get_sensors(app, sensors_uri, sensors_lastreading):
    with app.test_client() as app_client:
        response = app_client.get(sensors_uri)
        response_sensors = json.loads(response.data)['sensors']
        sensors_api = json.loads(json.dumps(sensors_lastreading))
        for s1, s2 in zip(response_sensors, sensors_api):
            s1.pop('uri')
            assert s1 == s2


@pytest.fixture
def sensor_uri(sensors, sensors_uri):
    sensor = sensors[0]
    return '{}/{}'.format(sensors_uri, sensor['id'])


def test_get_sensor(app, sensor_uri, sensors_lastreading):
    with app.test_client() as app_client:
        response = app_client.get(sensor_uri)
        response_sensor = json.loads(response.data)['sensor']
        sensor_api = json.loads(json.dumps(sensors_lastreading[0]))
        assert response_sensor == sensor_api


def test_put_sensor(app, sensors_uri, sensors_lastreading):
    sensor_api = sensors_lastreading[0]
    test_location = 'asdfjkl'
    sensor_api['location'] = test_location
    uri = '{}/{}'.format(sensors_uri, sensor_api['id'])

    with app.test_client() as app_client:
        response = app_client.put(uri, data=json.dumps({'sensor': sensor_api}), content_type='application/json')
        response_sensor = json.loads(response.data)
        sensor = json.loads(json.dumps({'sensor': sensor_api}))
        assert response_sensor == sensor
