import pytest
from pathlib import Path

from .database_provider import ConnectionStringProvider, DatabaseVolumeProvider, LocalConnectionStringProvider, MiovisionDBQueryProvider, MiovisionDBVolumeProvider, VolumeQueryProvider
from .volume_provider import Authenticator, CredentialsProvider, HtmlAuthenticator, HtmlVolumeProvider, HtmlVolumeScraper, LocalCredentialsProvider, VolumeProvider, VolumeScraper

def excel_files()->list[Path]:
    test_files_directory = Path('Granular Miovision Files')
    
    assert test_files_directory.exists(), f'Test directory {test_files_directory} does not exist'
    
    return [path for path in test_files_directory.iterdir()]

@pytest.fixture(scope="module")
def miovision_base_url()->str:
    return "https://datalink.miovision.com/studies/"


@pytest.fixture(scope='module')
def miovision_id_url(miovision_base_url,miovision_id)->str:
    return f'{miovision_base_url}{miovision_id}'

@pytest.fixture(scope="module")
def credentials()->CredentialsProvider:
    return LocalCredentialsProvider()

@pytest.fixture(scope="module")
def authenticator(credentials)->Authenticator:
    return HtmlAuthenticator(credentials=credentials)

@pytest.fixture(scope='module')
def scraper(authenticator)->VolumeScraper:
    return HtmlVolumeScraper(authenticator)


@pytest.fixture
def online_volume_provider(miovision_base_url, scraper)-> VolumeProvider:
    volume_provider = HtmlVolumeProvider(base_url=miovision_base_url,
                                         scraper=scraper)
    
    return volume_provider

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
def db_volume_provider(query_provider,connection_string_provider)->DatabaseVolumeProvider:
    return MiovisionDBVolumeProvider(connection_string_provider,query_provider)

def get_miovision_id(stem:str)->str:
    type_id = stem.split('-')
    assert len(type_id) == 2, "Stem is not of type '<label>-<id>'"
    return type_id[-1]

@pytest.mark.parametrize("path",excel_files())
def test_in_out_volumes(path: Path, online_volume_provider,db_volume_provider):
    miovision_id = get_miovision_id(path.stem)
    online_result = online_volume_provider.get_volume(miovision_id)
    db_result = db_volume_provider.return_volumes(path)
    
    assert online_result == db_result, f"Inconsistent result for {miovision_id}"