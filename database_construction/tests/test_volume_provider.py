import pytest
from .volume_provider import VolumeProvider, HtmlVolumeProvider, HtmlVolumeScraper, HtmlAuthenticator, LocalCredentialsProvider
from .volume_provider import CredentialsProvider, VolumeScraper, Authenticator, DirectionalVolumeAttr

@pytest.fixture(scope="module")
def miovision_base_url()->str:
    return "https://datalink.miovision.com/studies/"

@pytest.fixture(scope='module')
def miovision_id()->int:
    return 1230846

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
def volume_provider(miovision_base_url, scraper)-> VolumeProvider:
    volume_provider = HtmlVolumeProvider(base_url=miovision_base_url,
                                         scraper=scraper)
    
    return volume_provider

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


def test_authenticator(authenticator):
    path = authenticator.return_authentication_file()
    
    assert path.exists(), "Authentication file not created"

def test_scraper(scraper,miovision_id_url):
    direction_volumes = scraper.return_directions_volumes(miovision_id_url)

def test_provider(volume_provider,miovision_id, expected_result):
    result = volume_provider.get_volume(miovision_id)
    assert result == expected_result, f"{result} does not equal {expected_result}"