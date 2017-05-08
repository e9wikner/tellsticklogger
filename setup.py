from setuptools import setup, find_packages

setup(
    name='tellsticklogger',
    version='0.2',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    package_data={'tellsticklogger': ['*.ini']},
    install_requires=['click>=6.6', 'Flask>=0.11.1', 'tellcore-py>=1.1.3', 'plotly>=1.12.12'],
    author='Stefan Wikner',
    author_email='stefan.wikner@gmail.com',
    description='Logging package for Tellstick Duo',
    entry_points='''
        [console_scripts]
        tellstick_logger=tellsticklogger.core:cli_start_logger
        tellstick_locate_sensor=tellsticklogger.core:cli_set_sensor_location
        tellstick_csv_to_plotly=tellsticklogger.scripts.tellstick_csv_to_plotly:cli
    '''
)
