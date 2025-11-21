from typing import Protocol
from .volume_provider import DirectionalVolumeAttr
from pathlib import Path
from psycopg2 import connect
from dotenv import load_dotenv
from providers.tables_providers import PredefinedTableNames, PredefinedTableLabels, StudiesDirectionsTableColumns, StudiesTableColumns
import os
from psycopg2.sql import Composed, SQL, Identifier
from enum import StrEnum

class MiovisionDBProviderConfig(StrEnum):
    pedway_indicator = "way"

class VolumeQueryProvider(Protocol):
    def get_roadway_volume_query(self)->Composed:...
    
    def get_pedway_volume_query(self)->Composed:...

class DatabaseVolumeProvider(Protocol):
    def return_volumes(self, file_path: Path)->dict[str,DirectionalVolumeAttr]:...

class ConnectionStringProvider(Protocol):
    def get_connection_string(self)->str:...

class LocalConnectionStringProvider:
    def __init__(self, env_key) -> None:
        self._env_key_label = env_key
        load_dotenv()
    
    def get_connection_string(self)->str:
        if self._env_key_label not in os.environ:
            raise KeyError(f"{self._env_key_label} not found in environment variables.")
        
        return os.environ[self._env_key_label]

class MiovisionDBQueryProvider:
    def __init__(self) -> None:
        self._roadway_query = SQL("""
                          SELECT dt.{direction_type_name},
                                    get_out_volume(s.{study_miovision_id},dt.directional_id),
                                    get_in_volume(s.miovision_id, dt.directional_id)
                            FROM {studies_table} s
                            JOIN {sd} sd on s.{study_miovision_id} = sd.{sd_miovision_id}
                            JOIN {directions_table} dt on dt.id = sd.{direction_type_id}
                            WHERE s.{study_miovision_id} = %s;
                          """).format(
                              direction_type_name = Identifier(PredefinedTableLabels.direction_types.value),
                              study_miovision_id = Identifier(StudiesTableColumns.miovision_id.value),
                              studies_table = Identifier(PredefinedTableNames.studies.value),
                              sd = Identifier(PredefinedTableNames.studies_directions.value),
                              sd_miovision_id = Identifier(StudiesDirectionsTableColumns.miovision_id.value),
                              directions_table = Identifier(PredefinedTableNames.direction_types.value),
                              direction_type_id = Identifier(StudiesDirectionsTableColumns.direction_type_id.value)
                          )
        
        self._pedway_query = SQL("""
                          SELECT dt.{direction_type_name},
                                    COALESCE(pedway_out_volume_calculation(s.{study_miovision_id},dt.directional_id), 0),
                                    COALESCE(pedway_in_volume_calculation(s.miovision_id, dt.directional_id), 0)
                            FROM {studies_table} s
                            JOIN {sd} sd on s.{study_miovision_id} = sd.{sd_miovision_id}
                            JOIN {directions_table} dt on dt.id = sd.{direction_type_id}
                            WHERE s.{study_miovision_id} = %s;
                          """).format(
                              direction_type_name = Identifier(PredefinedTableLabels.direction_types.value),
                              study_miovision_id = Identifier(StudiesTableColumns.miovision_id.value),
                              studies_table = Identifier(PredefinedTableNames.studies.value),
                              sd = Identifier(PredefinedTableNames.studies_directions.value),
                              sd_miovision_id = Identifier(StudiesDirectionsTableColumns.miovision_id.value),
                              directions_table = Identifier(PredefinedTableNames.direction_types.value),
                              direction_type_id = Identifier(StudiesDirectionsTableColumns.direction_type_id.value)
                          )

    def get_roadway_volume_query(self):
        return self._roadway_query
    
    def get_pedway_volume_query(self)->Composed:
        return self._pedway_query

class MiovisionDBVolumeProvider:
    def __init__(self, connection_string: ConnectionStringProvider, query_provider: MiovisionDBQueryProvider) -> None:
        self._connection = connect(connection_string.get_connection_string())
        self._roadway_query = query_provider.get_roadway_volume_query()
        self._pedway_query = query_provider.get_pedway_volume_query()
        self._cursor = self._connection.cursor()
    
    def shutdown_connection(self)->None:
        self._cursor.close()
        self._connection.close()
    
    def _get_study_type_miovision_id(self, file_stem:str)->tuple[str,int]:
        # Expect file_stemm to be of format "<station>-<id>"
        study_type_id = file_stem.split('-')
        assert len(study_type_id) == 2, f"Provided stem {file_stem} not in format of '<station>-<id>'"
        
        return str(study_type_id[0]), int(study_type_id[-1])
    
    def return_volumes(self, file_path: Path)->dict[str,DirectionalVolumeAttr]:
        study_type, miovision_id = self._get_study_type_miovision_id(file_path.stem)
        
        if MiovisionDBProviderConfig.pedway_indicator.value in study_type:
            self._cursor.execute(self._pedway_query,[miovision_id])
        else:
            self._cursor.execute(self._roadway_query,[miovision_id])
        results = self._cursor.fetchall()
        volume_mapping : dict[str,DirectionalVolumeAttr] = {}
        
        for direction_name, out_volume, in_volume in results:
            if not isinstance(direction_name,str):
                raise Exception("direction_name is not a string")
            
            if not isinstance(out_volume, int):
                raise Exception("out_volume is not an integer")
            
            if not isinstance(in_volume, int):
                raise Exception("in_volume is not an integer")
            
            if in_volume == 0:
                continue
            
            directional_attributes = DirectionalVolumeAttr(total_volume = out_volume+in_volume,
                                                           in_volume = in_volume,
                                                           out_volume = out_volume)
            volume_mapping[direction_name] = directional_attributes
            
        return volume_mapping