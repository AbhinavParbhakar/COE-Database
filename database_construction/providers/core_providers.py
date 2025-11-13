from typing import Protocol, TypedDict, Any
from .types_providers import BaseFolderValidator
from pathlib import Path
import pandas as pd
from .tables_providers import PredefinedTableNames, StudiesTableColumns
from .database_providers import DatabaseConnection
from .extraction_providers import StudiesExtractor, DirectionsExtractor


class TransactionContext:
    def __init__(self) -> None:
        self.paths_studies_mapping : dict[Path,list[str]] = {}
        self.all_movements : list[str]
        self.all_vehicles : list[str]

class CoreDataProvider(Protocol):
    def write_data(self)->None:...
    """
    Write data into database
    """

class StudiesDirectionsProvider:
    def __init__(self, base_validator: BaseFolderValidator, context: TransactionContext, database_connection : DatabaseConnection, directions_extractor : DirectionsExtractor) -> None:
        self._paths = base_validator.get_files()
        self._context = context
        self._db_connection = database_connection
        self._extractor = directions_extractor
        pass

class StudiesProvider:
    def __init__(self, base_validator: BaseFolderValidator, database_connection : DatabaseConnection, studies_extractor : StudiesExtractor) -> None:
        self._paths = base_validator.get_files()
        self._db_connection = database_connection
        self._studies_extractor = studies_extractor
    
    def write_data(self)->None:
        for path in self._paths:
            study_fields = self._studies_extractor.extract_fields(path)
            self._db_connection.insert_new_information(
                table_name=PredefinedTableNames.studies.value,
                labels=[
                    StudiesTableColumns.miovision_id.value,
                    StudiesTableColumns.latitude.value,
                    StudiesTableColumns.longitude.value,
                    StudiesTableColumns.location_name.value,
                    StudiesTableColumns.project_name.value,
                    StudiesTableColumns.study_date.value,
                    StudiesTableColumns.study_duration.value,
                    StudiesTableColumns.study_type.value,
                    StudiesTableColumns.study_name.value
                ],
                values=[
                    study_fields.miovision_id,
                    study_fields.latitude,
                    study_fields.longitude,
                    study_fields.location_name,
                    study_fields.project_name,
                    study_fields.study_date.date,
                    study_fields.study_duration,
                    study_fields.study_date,
                    study_fields.study_name
                ]
            )