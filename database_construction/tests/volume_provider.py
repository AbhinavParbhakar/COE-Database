from typing import Protocol
from playwright.sync_api import sync_playwright
from playwright.sync_api import Playwright, Page
from enum import StrEnum
from pathlib import Path
from dotenv import load_dotenv
import os

class AuthenticationStorageConfig(StrEnum):
    path_name = 'auth.json'

class AuthenticationScrapingConfig(StrEnum):
    email_locator_text = "input[name=username]"
    email_submit_locator_text = "button._button-login-id"
    email_password_locator_text = "input[name=password]"
    login_submit_locator_text = "button._button-login-password"
    auth_url = "https://datalink.miovision.com/"

class VolumeScrapingConfig(StrEnum):
    volume_locator_text = 'text.direction_total'
    volume_direction_id_name = 'data-direction'
    
class LocalCredentials(StrEnum):
    username = "MIOVISION_USERNAME"
    password = "MIOVISION_PASSWORD"
    
class CredentialsProvider(Protocol):
    def get_username(self)->str:...
    
    def get_password(self)->str:...

class LocalCredentialsProvider:
    def __init__(self) -> None:
        load_dotenv()
        if LocalCredentials.username.value not in os.environ:
            raise Exception(f'{LocalCredentials.username.value} not found in .env file.')
        if LocalCredentials.password.value not in os.environ:
            raise Exception(f'{LocalCredentials.password.value} not found in .env file.')
    
    def get_username(self)->str:
        return os.environ[LocalCredentials.username.value]

    def get_password(self)->str:
        return os.environ[LocalCredentials.password.value]
    
class VolumeProvider(Protocol):
    def get_volume(self,miovision_id:str)->dict[str,int]:...

class VolumeScraper(Protocol):
    def return_directions_volumes(self,url:str)->tuple[list[str],list[int]]:...

class Authenticator(Protocol):
    def return_authentication_file(self)->Path:...

class HtmlAuthenticator:
    def __init__(self, credentials: CredentialsProvider, auth_file=AuthenticationStorageConfig.path_name.value) -> None:
        self._auth_file = Path(auth_file)
        self._authenticated = False
        self._username = credentials.get_username()
        self._password = credentials.get_password()
    
    def _authenticate(self)->None:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            
            page.goto(AuthenticationScrapingConfig.auth_url.value)
            
            page.locator(AuthenticationScrapingConfig.email_locator_text.value).type(self._username)
            page.locator(AuthenticationScrapingConfig.email_submit_locator_text.value).click()
            page.locator(AuthenticationScrapingConfig.email_password_locator_text.value).type(self._password)
            page.locator(AuthenticationScrapingConfig.login_submit_locator_text.value).click()
            
            page.close()
            
            context.storage_state(path=self._auth_file)
        self._authenticated = True
    
    def return_authentication_file(self)->Path:
        if not self._authenticated:
            self._authenticate()
        return self._auth_file

class HtmlVolumeScraper:
    def __init__(self, authenticator: Authenticator) -> None:
        self._authentication_storage_session_path = authenticator.return_authentication_file()

    def return_directions_volumes(self,url:str)->tuple[list[str],list[int]]:
        directions : list[str] = []
        volumes : list[int] = []
        
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(storage_state=self._authentication_storage_session_path)
            page = context.new_page()
            
            page.goto(url)
            volume_locators = page.locator(VolumeScrapingConfig.volume_locator_text.value).all()
            for locator in volume_locators:
                volume_text = locator.text_content()
                if volume_text is None:
                    raise Exception(f"Text from locator {VolumeScrapingConfig.volume_locator_text} yielded None")
                # Text expected in the form "Total : <count>"
                total_volume_list = volume_text.split(':')
                assert len(total_volume_list) == 2, "Text scraped from Volume Locator doesn't match 'Total: <count>' format."
                volumes.append(int(total_volume_list[-1]))
                
                direction_id = locator.get_attribute(VolumeScrapingConfig.volume_direction_id_name.value)
                
                if direction_id is None:
                    raise Exception(f"{VolumeScrapingConfig.volume_direction_id_name.value} attribute not found")
                else:
                    directions.append(direction_id)
        
        return (directions,volumes)

class HtmlVolumeProvider:
    def __init__(self, base_url:str, scraper: VolumeScraper) -> None:
        self._base_url = base_url
        self._scraper = scraper
        self._direction_name_mapping = {
            1 : "Southbound",
            2 : "Southwestbound",
            3 : "Westbound",
            4 : "Northwestbound",
            5 : "Northbound",
            6 : "Northeastbound",
            7 : "Eastbound",
            8 : "Southeastbound"
        }
        
    def get_volume(self, miovision_id: str)->dict[str,int]:
        directions_volumes = self._scraper.return_directions_volumes(f'{self._base_url}{miovision_id}')
        
        try:
            return {
                self._direction_name_mapping[int(direction)] : int(volume) for direction, volume in directions_volumes
            }
        except KeyError as e:
            raise Exception(f'Direction_id returned from VolumeScraper not found in mapping: {e}')
        except Exception as e:
            raise Exception(f'Exception raised during volume provider processing: {e}')