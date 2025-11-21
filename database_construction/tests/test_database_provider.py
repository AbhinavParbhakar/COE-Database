import pytest
from .database_provider import DatabaseVolumeProvider, ConnectionStringProvider, VolumeQueryProvider
from .database_provider import MiovisionDBVolumeProvider, LocalConnectionStringProvider, MiovisionDBQueryProvider
from pathlib import Path
from .volume_provider import DirectionalVolumeAttr

@pytest.fixture(scope='module')
def env_key()->str:
    return "LOCAL_DATABASE_URL"

@pytest.fixture(scope='module')
def connection_string_provider(env_key)->ConnectionStringProvider:
    return LocalConnectionStringProvider(env_key)

@pytest.fixture(scope='module')
def query_provider()->VolumeQueryProvider:
    return MiovisionDBQueryProvider()

@pytest.fixture(scope='module')
def volume_provider(query_provider,connection_string_provider)->DatabaseVolumeProvider:
    return MiovisionDBVolumeProvider(connection_string_provider,query_provider)

@pytest.fixture(scope='module')
def dummy_path()->Path:
    return Path('Granular Miovision Files/TMC-1230846.xlsx')

@pytest.fixture(scope='module')
def expected_result()->dict[str,DirectionalVolumeAttr]:
    return {
        "Southbound":{
            'total_volume':17277,
            'in_volume':9,
            'out_volume':17268
        },
        "Westbound":{
            'total_volume':20653,
            'in_volume':10185,
            'out_volume':10468
        },
        "Northbound":{
            'total_volume':21652,
            'in_volume':21650,
            'out_volume':2
        },
        "Eastbound":{
            'total_volume':18768,
            'in_volume':7331,
            'out_volume':11437
        }
    }

def test_db_volume(dummy_path, volume_provider, expected_result):
    result = volume_provider.return_volumes(dummy_path)
    assert result == expected_result, f"{result} does not match {expected_result}"