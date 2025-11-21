from typing import Protocol, TypedDict
from playwright.sync_api import sync_playwright, Locator
from enum import StrEnum
from pathlib import Path
from dotenv import load_dotenv
import os

class DirectionalVolumeAttr(TypedDict):
    total_volume : int
    in_volume : int
    out_volume : int

class AuthenticationStorageConfig(StrEnum):
    path_name = 'auth.json'

class AuthenticationScrapingConfig(StrEnum):
    email_locator_text = "input[name=username]"
    email_submit_locator_text = "button._button-login-id"
    email_password_locator_text = "input[name=password]"
    login_submit_locator_text = "button._button-login-password"
    auth_url = "https://datalink.miovision.com/"

class VolumeScrapingConfig(StrEnum):
    total_volume_locator_text = 'text.direction_total'
    in_volume_locator_text = 'text.enter_total'
    out_volume_locator_text = 'text.exit_total'
    volume_direction_id_name = 'data-direction'
    
class LocalCredentials(StrEnum):
    username = "MIOVISION_USERNAME"
    password = "MIOVISION_PASSWORD"
    
class CredentialsProvider(Protocol):
    def get_username(self)->str:...
    
    def get_password(self)->str:...

class VolumeProvider(Protocol):
    def get_volume(self,miovision_id:str)->dict[str,DirectionalVolumeAttr]:...

class VolumeScraper(Protocol):
    def return_directions_volumes(self,url:str)->list[tuple[str,DirectionalVolumeAttr]]:...

class Authenticator(Protocol):
    def return_authentication_file(self)->Path:...

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

    def _parse_volume(self,volume_string:str|None)->int:
        if volume_string is None:
            raise Exception("None passed in as volume_string")

        # Expect "<label> : <volume>" structure for volume_string
        volume_label_value = volume_string.split(":")
        assert len(volume_label_value) == 2, "Text scraped from Volume Locator doesn't match '<label>: <count>' format."
        
        return int(volume_label_value[-1])
    
    def _parse_directional_id(self,locator: Locator)->str:
        direction_id = locator.get_attribute(VolumeScrapingConfig.volume_direction_id_name.value)
        
        if direction_id is None:
            raise Exception(f"{VolumeScrapingConfig.volume_direction_id_name.value} attribute not found")
        
        return direction_id

    def return_directions_volumes(self,url:str)->list[tuple[str,DirectionalVolumeAttr]]:
        direction_volumes : list[tuple[str,DirectionalVolumeAttr]] = []
        in_volume_mapping : dict[str,int] = {}
        out_volume_mapping : dict[str,int] = {}
        
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(storage_state=self._authentication_storage_session_path)
            page = context.new_page()
            
            page.goto(url)
            
            in_volume_locators = page.locator(VolumeScrapingConfig.in_volume_locator_text.value).all()
            out_volume_locators = page.locator(VolumeScrapingConfig.out_volume_locator_text).all()
            total_volume_locators = page.locator(VolumeScrapingConfig.total_volume_locator_text.value).all()
            
            for locator in in_volume_locators:
                in_volume_mapping[self._parse_directional_id(locator)] = self._parse_volume(locator.text_content())
            
            for locator in out_volume_locators:
                out_volume_mapping[self._parse_directional_id(locator)] = self._parse_volume(locator.text_content())
                
            
            for locator in total_volume_locators:
                total_volume = self._parse_volume(locator.text_content())
                directional_id = self._parse_directional_id(locator)

                try:
                    in_volume = in_volume_mapping[directional_id]
                    out_volume = out_volume_mapping[directional_id]
                    volume_attr = DirectionalVolumeAttr(total_volume=total_volume,
                                                        in_volume=in_volume,
                                                        out_volume=out_volume)
                    
                    direction_volumes.append((directional_id,volume_attr))
                except KeyError as e:
                    raise KeyError(f"Directional_id for total_volume_locator not found in mapping: {e}")
                
        return direction_volumes

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
        
    def get_volume(self, miovision_id: str)->dict[str,DirectionalVolumeAttr]:
        directions_volumes = self._scraper.return_directions_volumes(f'{self._base_url}{miovision_id}')
        volume_mapping  : dict[str, DirectionalVolumeAttr]= {}
        
        for direction_id, volume_attributes in directions_volumes:
            if volume_attributes["in_volume"] != 0:
                try:
                    direction_name = self._direction_name_mapping[int(direction_id)]
                    volume_mapping[direction_name] = volume_attributes
                except KeyError as e:
                    raise Exception(f'Direction_id returned from VolumeScraper not found in mapping: {e}')
                except Exception as e:
                    raise Exception(f'Exception raised during volume provider processing: {e}')
        
        return volume_mapping