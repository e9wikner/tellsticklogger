#!/usr/bin/env python
# coding: utf-8
import logging
from collections import defaultdict, namedtuple
from datetime import datetime
from statistics import mean

import click
from plotly.plotly import plot
from plotly.graph_objs import Scattergl
import tellcore.constants
import tellsticklogger


Points = namedtuple('Points', ['x', 'y'])


def points(rows):
    x = [datetime.fromtimestamp(ts) for ts in sensor['timestamps']]
    y = [float(r['value']) for r in rows]
    return Points(x, y)


def hour_to_values_dict(datetimes, values):
    hour_values = defaultdict(list)
    for dt, value in zip(datetimes, values):
        hour_values[datetime(dt.year, dt.month, dt.day, hour=dt.hour)].append(value)

    return hour_values


def hourly_mean_points(datetimes, values):
    hour_to_mean_value_dict = {
        hour: mean(values) for hour, values in hour_to_values_dict(datetimes, values).items()}
    x = sorted(hour_to_mean_value_dict)
    y = [hour_to_mean_value_dict[x_i] for x_i in x]
    return Points(x, y)


def day_to_values_dict(datetimes, values):
    daily_values = defaultdict(list)
    for dt, value in zip(datetimes, values):
        daily_values[dt.date()].append(value)

    return daily_values


def daily_mean_points(datetimes, values):
    day_to_mean_value_dict = {
        day: mean(values) for day, values in day_to_values_dict(datetimes, values).items()}
    x = sorted(day_to_mean_value_dict)
    y = [day_to_mean_value_dict[x_i] for x_i in x]
    return Points(x, y)


@click.command(help='Update logged temperature and humidity Plotly plots')
@click.option('--csvpath', default='.', help='Path where csv files are found')
@click.option('--browse', is_flag=True, help='Open browser and show plots')
def cli(csvpath, browse):
    logger = logging.basicConfig(level=logging.INFO)
    csv_to_plotly(csvpath=csvpath, browse=browse)


def csv_to_plotly(csvpath='.', browse=False):

    sensors = tellsticklogger.sensors(csvpath=csvpath, include_all_readings=True)
    if len(sensors) == 0:
        print('no sensors found in ' + csvpath)
        return

    sensor_location_to_humidity = {s['location']:
            (tuple(datetime.fromtimestamp(ts) for ts in s['timestamps']), s['values'])
            for s in sensors
            if s['valuetype'].lower() == 'humidity'
    }
    sensor_location_to_temperature = {s['location']:
            (tuple(datetime.fromtimestamp(ts) for ts in s['timestamps']), s['values'])
            for s in sensors
            if s['valuetype'].lower() == 'temperature'
    }

    sensor_location_to_hourly_mean_humidity_points = {
        loc + '_hour': hourly_mean_points(*sensor_location_to_humidity[loc])
        for loc in sensor_location_to_humidity}

    sensor_location_to_hourly_mean_temperature_points = {
        loc + '_hour': hourly_mean_points(*sensor_location_to_temperature[loc])
        for loc in sensor_location_to_temperature}

    sensor_location_to_daily_mean_humidity_points = {
        loc + '_day': daily_mean_points(*sensor_location_to_humidity[loc])
        for loc in sensor_location_to_humidity}

    sensor_location_to_daily_mean_temperature_points = {
        loc + '_day': daily_mean_points(*sensor_location_to_temperature[loc])
        for loc in sensor_location_to_temperature}

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

    tempplot = plot(scatter_temperatur, filename='templog i huset',
                    fileopt='overwrite', auto_open=browse)
    fuktplot = plot(scatter_fuktighet, filename='fuktlog i huset',
                    fileopt='overwrite', auto_open=browse)

    print(tempplot, fuktplot)


if __name__=='__main__':
    cli()
