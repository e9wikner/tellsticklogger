#!/usr/bin/env python
# coding: utf-8
from datetime import datetime
import sqlite3

import click
from plotly.plotly import plot
from plotly.graph_objs import Scatter

from tellcore.constants import *


DB_CONNECTION = None


def fetch_sensor_rows(table, valuetype):
    with DB_CONNECTION:
        return DB_CONNECTION.execute("SELECT timestamp, value from %s WHERE type=?" % table,
                                     str(valuetype)).fetchall()


def rows_to_xy(rows):
    x = [datetime.fromtimestamp(r['timestamp']) for r in rows]
    y = [float(r['value']) for r in rows]
    return x, y

@click.command(help='Update logged temperature and humidity Plotly plots')
@click.option('--database', help='Path to sensor database')
@click.option('--browse', is_flag=True, help='Open browser and show plots')
def cli(database, browse):

    global DB_CONNECTION
    DB_CONNECTION = sqlite3.connect(database)
    DB_CONNECTION.row_factory = sqlite3.Row

    humidities_rows = {
        'bokhylla' : fetch_sensor_rows('sensor_180', TELLSTICK_HUMIDITY),
        'badrum'   : fetch_sensor_rows('sensor_226', TELLSTICK_HUMIDITY),
        'balkong'  : fetch_sensor_rows('sensor_248', TELLSTICK_HUMIDITY)
        }

    temperatures_rows = {
        'bokhylla' : fetch_sensor_rows('sensor_180', TELLSTICK_TEMPERATURE),
        'badrum'   : fetch_sensor_rows('sensor_226', TELLSTICK_TEMPERATURE),
        'balkong'  : fetch_sensor_rows('sensor_248', TELLSTICK_TEMPERATURE)
        }

    humidities_xy = {k: rows_to_xy(v) for k, v in humidities_rows.items()}
    temperatures_xy = {k: rows_to_xy(v) for k, v in temperatures_rows.items()}

    scatter_temperatur = [Scatter(x=xy[0], y=xy[1], name=name)
                          for name, xy in temperatures_xy.items()]
    scatter_fuktighet = [Scatter(x=xy[0], y=xy[1], name=name)
                         for name, xy in humidities_xy.items()]

    tempplot = plot(scatter_temperatur, filename='templog i lägenheten',
                    fileopt='overwrite', auto_open=browse)
    fuktplot = plot(scatter_fuktighet, filename='fuktlog i lägenheten',
                    fileopt='overwrite', auto_open=browse)

    print(tempplot, fuktplot)
    DB_CONNECTION.close()


if __name__=='__main__':
    cli()
