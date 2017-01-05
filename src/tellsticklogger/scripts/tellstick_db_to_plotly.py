#!/usr/bin/env python
# coding: utf-8
from collections import defaultdict, namedtuple
from datetime import datetime
import sqlite3
from statistics import mean

import click
from plotly.plotly import plot
from plotly.graph_objs import Scattergl
import tellcore.constants


DB_CONNECTION = None
Points = namedtuple('Points', ['x', 'y'])


def fetch_sensor_rows(table, valuetype):
    with DB_CONNECTION:
        return DB_CONNECTION.execute("SELECT timestamp, value from %s WHERE type=?" % table,
                                     str(valuetype)).fetchall()


def points(rows):
    x = [datetime.fromtimestamp(r['timestamp']) for r in rows]
    y = [float(r['value']) for r in rows]
    return Points(x, y)


def hour_to_values_dict(rows):
    hour_values = defaultdict(list)
    for r in rows:
        dt = datetime.fromtimestamp(r['timestamp'])
        value = float(r['value'])
        hour_values[datetime(dt.year, dt.month, dt.day, hour=dt.hour)].append(value)

    return hour_values


def hourly_mean_points(rows):
    hour_to_mean_value_dict = {
        hour: mean(values) for hour, values in hour_to_values_dict(rows).items()}
    x = sorted(hour_to_mean_value_dict)
    y = [hour_to_mean_value_dict[x_i] for x_i in x]
    return Points(x, y)


def day_to_values_dict(rows):
    daily_values = defaultdict(list)
    for r in rows:
        datetime_ = datetime.fromtimestamp(r['timestamp'])
        value = float(r['value'])
        daily_values[datetime_.date()].append(value)

    return daily_values


def daily_mean_points(rows):
    day_to_mean_value_dict = {
        day: mean(values) for day, values in day_to_values_dict(rows).items()}
    x = sorted(day_to_mean_value_dict)
    y = [day_to_mean_value_dict[x_i] for x_i in x]
    return Points(x, y)


@click.command(help='Update logged temperature and humidity Plotly plots')
@click.argument('database')
@click.option('--browse', is_flag=True, help='Open browser and show plots')
def cli(database, browse):

    global DB_CONNECTION
    DB_CONNECTION = sqlite3.connect(database)
    DB_CONNECTION.row_factory = sqlite3.Row

    sensor_location_to_humidity_rows = {
        'bokhylla': fetch_sensor_rows('sensor_180', tellcore.constants.TELLSTICK_HUMIDITY),
        'badrum': fetch_sensor_rows('sensor_226', tellcore.constants.TELLSTICK_HUMIDITY),
        'balkong': fetch_sensor_rows('sensor_248', tellcore.constants.TELLSTICK_HUMIDITY)
    }

    sensor_location_to_temperature_rows = {
        'bokhylla': fetch_sensor_rows('sensor_180', tellcore.constants.TELLSTICK_TEMPERATURE),
        'badrum': fetch_sensor_rows('sensor_226', tellcore.constants.TELLSTICK_TEMPERATURE),
        'balkong': fetch_sensor_rows('sensor_248', tellcore.constants.TELLSTICK_TEMPERATURE)
    }

    sensor_location_to_hourly_mean_humidity_points = {
        loc + '_hour': hourly_mean_points(sensor_location_to_humidity_rows[loc])
        for loc in sensor_location_to_humidity_rows}

    sensor_location_to_hourly_mean_temperature_points = {
        loc + '_hour': hourly_mean_points(sensor_location_to_temperature_rows[loc])
        for loc in sensor_location_to_temperature_rows}

    sensor_location_to_daily_mean_humidity_points = {
        loc + '_day': daily_mean_points(sensor_location_to_humidity_rows[loc])
        for loc in sensor_location_to_humidity_rows}

    sensor_location_to_daily_mean_temperature_points = {
        loc + '_day': daily_mean_points(sensor_location_to_temperature_rows[loc])
        for loc in sensor_location_to_temperature_rows}

    def merge_dicts(dicts):
        """Given dicts, merge them into a new dict as a shallow copy."""
        merged_dict = dicts[0].copy()
        for d in dicts[1:]:
            merged_dict.update(d)
        return merged_dict

    sensor_location_to_humidities = merge_dicts((
        sensor_location_to_hourly_mean_humidity_points,
        sensor_location_to_daily_mean_humidity_points
    ))
    sensor_location_to_temperatures = merge_dicts((
        sensor_location_to_hourly_mean_temperature_points,
        sensor_location_to_daily_mean_temperature_points
    ))

    scatter_temperatur = [Scattergl(x=points.x, y=points.y, name=name)
                          for name, points in sensor_location_to_temperatures.items()]
    scatter_fuktighet = [Scattergl(x=points.x, y=points.y, name=name)
                         for name, points in sensor_location_to_humidities.items()]

    tempplot = plot(scatter_temperatur, filename='templog i lägenheten - medel',
                    fileopt='overwrite', auto_open=browse)
    fuktplot = plot(scatter_fuktighet, filename='fuktlog i lägenheten - medel',
                    fileopt='overwrite', auto_open=browse)

    print(tempplot, fuktplot)
    DB_CONNECTION.close()


if __name__=='__main__':
    cli()
