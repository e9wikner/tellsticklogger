from flask import json
import pytest

import tellsticklogger.restserver


URI_TELLSTICK_API = '/tellsticklogger/api'

@pytest.fixture
def app():
    app = tellsticklogger.restserver.app
    app.config['TESTING'] = True
    return app


@pytest.fixture(params=['v0.1',])
def sensors_uri(request):
    return '/'.join((URI_TELLSTICK_API, request.param, 'sensors'))

def test_get_sensors(app, sensors_uri, sensors):
    with app.test_client() as app_client:
        response = app_client.get(sensors_uri)
        response_sensors = json.loads(response.data)['sensors']
        sensors = json.loads(json.dumps(sensors))
        for s1, s2 in zip(response_sensors, sensors):
            s1.pop('uri')
            assert s1 == s2


def test_get_sensor(app, sensors_uri, sensors):
    with app.test_client() as app_client:
        sensor = sensors[0]
        uri = '{}/{}'.format(sensors_uri, sensor['id'])
        response = app_client.get(uri)
        response_sensor = json.loads(response.data)['sensor']
        sensor = json.loads(json.dumps(sensor))
        assert response_sensor == sensor


def test_put_sensor(app, sensors_uri, sensors):
    sensor = sensors[0]
    test_location = 'asdfjkl'
    sensor['location'] = test_location
    uri = '{}/{}'.format(sensors_uri, sensor['id'])

    with app.test_client() as app_client:
        response = app_client.put(uri, data=json.dumps({'sensor': sensor}), content_type='application/json')
        response_sensor = json.loads(response.data)
        sensor = json.loads(json.dumps({'sensor': sensor}))
        assert response_sensor == sensor
