import subprocess

import pytest

import pip
is_installed = 'tellsticklogger' in pip.get_installed_distributions().__str__()

@pytest.mark.skipif(not is_installed, reason='Install to run skript test')
@pytest.mark.parametrize('script', ['tellstick_logger', 'tellstick_db_to_plotly'])
def test_command_tellstick_sensor_monitor(script):
    '''
    Test that
    - the command can be called from the command line.
    '''

    completedprocess = subprocess.run(
        (script, '--help'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    assert not completedprocess.stderr
    assert script in completedprocess.stdout
