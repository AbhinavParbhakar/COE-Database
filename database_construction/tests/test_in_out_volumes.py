import pytest
from .test_volume_provider import VolumeProvider, HtmlVolumeProvider, HtmlVolumeScraper, HtmlAuthenticator, LocalCredentialsProvider

@pytest.fixture
def test_miovision_base_url()->str:
    return "https://datalink.miovision.com/studies/"

@pytest.fixture
def test_miovision_volume_scraper(test_miovision_base_url)-> VolumeProvider:
    credentials = LocalCredentialsProvider()
    authenticator = HtmlAuthenticator(credentials=credentials)
    scraper = HtmlVolumeScraper(authenticator=authenticator)
    volume_provider = HtmlVolumeProvider(base_url=test_miovision_base_url,
                                         scraper=scraper)
    
    return volume_provider