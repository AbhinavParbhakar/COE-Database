import tables
from providers import MovementsProvider, VehiclesProvider, DirectionsProvider
from providers import BaseFolderValidator
from providers import InformationConfiguration
from pathlib import Path

if __name__ == "__main__":
    base_folder_path = Path('Granular Miovision Files')
    base_folder_validator = BaseFolderValidator(base_folder_path,'.xlsx')
