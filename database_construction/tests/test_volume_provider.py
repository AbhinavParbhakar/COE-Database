import pytest
from .volume_provider import VolumeProvider, HtmlVolumeProvider, HtmlVolumeScraper, HtmlAuthenticator, LocalCredentialsProvider
from .volume_provider import CredentialsProvider, VolumeScraper, Authenticator

@pytest.fixture(scope="module")
def miovision_base_url()->str:
    return "https://datalink.miovision.com/studies/"

@pytest.fixture(scope='module')
def miovision_id()->int:
    return 1311749

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
def test_miovision_volume_provider(miovision_base_url, scraper)-> VolumeProvider:
    volume_provider = HtmlVolumeProvider(base_url=miovision_base_url,
                                         scraper=scraper)
    
    return volume_provider

def test_authenticator(authenticator):
    path = authenticator.return_authentication_file()
    
    assert path.exists(), "Authentication file not created"

def test_scraper(scraper,miovision_id_url):
    directions, volumes = scraper.return_directions_volumes(miovision_id_url)
    
    assert len(directions) > 0, "Zero directions returned"
    assert len(volumes) > 0, "Zero Volumes returned"
    assert len(directions) == len(volumes), "Unequal values of volumes and directions"
    
