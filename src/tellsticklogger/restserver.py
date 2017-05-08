#!flask/bin/python
import flask

from . import core


app = flask.Flask(__name__, static_url_path='')
app.config['CSVPATH'] = '.'


def make_public_sensor(sensor):
    new_sensor = {}
    for key in sensor:
        if key == 'id':
            new_sensor['uri'] = flask.url_for('get_sensor', sensor_id=sensor['id'], _external=True)
        new_sensor[key] = sensor[key]
    return new_sensor


@app.route('/tellsticklogger/api/v0.1/sensors', methods=['GET'])
def get_sensors():
    return flask.jsonify({'sensors': [make_public_sensor(s)
                          for s in core.sensors(app.config['CSVPATH'])]})


@app.route('/tellsticklogger/api/v0.1/sensors/<int:sensor_id>', methods=['GET'])
def get_sensor(sensor_id):
    sensors = [s for s in core.sensors(app.config['CSVPATH']) if s['id'] == sensor_id]
    if len(sensors) == 0:
        flask.abort(404)

    return flask.jsonify({'sensor': sensors[0]})


@app.route('/tellsticklogger/api/v0.1/sensors/<int:sensor_id>', methods=['PUT'])
def put_sensor(sensor_id):
    sensors = core.sensors(app.config['CSVPATH'])
    if len(sensors) == 0:
        flask.abort(404)

    sensor = [s for s in sensors if s['id'] == sensor_id][0]

    if not flask.request.json:
        flask.abort(400)
    if 'location' in flask.request.json and type(flask.request.json['location']) is not str:
        flask.abort(400)

    sensor['location'] = flask.request.json.get('sensor')['location']
    app.logger.debug('set sensor {id} location: {location}'.format(**sensor))
    core.set_sensor_location(sensor, csvpath=app.config['CSVPATH'])
    return flask.jsonify({'sensor': sensor})
