from typing import Protocol, Any
from .types_providers import BaseFolderValidator
from .tables_providers import PredefinedTableNames, StudiesTableColumns, StudiesDirectionsTableColumns, PredefinedTableLabels, MovementsDirectionsTableColumns
from .tables_providers import GranularCountsTableColumns, MovementVehiclesTableColumns
from .database_providers import DatabaseConnection, DatabaseUpdater
from .extraction_providers import StudiesExtractor, DirectionsExtractor, MovementsExtractor, GranularExtractor
import tqdm


class TransactionContext:
    def __init__(self, db_connection : DatabaseConnection) -> None:
        self._direction_name_id_mapping : dict[str,int] = {}
        self._movement_name_id_mapping : dict[str,int] = {}
        self._vehicle_name_id_mapping : dict[str, int] = {}
        
        self._path_directions_mapping : dict[str,set[str]] = {}
        self._path_movements_mapping : dict[str,set[str]] = {}
        
        self._miovision_studies_directions_id_mapping : dict[tuple,int] = {}
        self._studies_direction_movement_id_mapping : dict[tuple,int] = {}
        self._studies_dir_mov_veh_id_mapping : dict[tuple,int] = {}
        
        self._db_connection = db_connection

    def update_dir_mov_veh_id_mapping(self, miovision_id: int, direction_name: str, movement_name : str, vehicle_name: str, id: int) -> None:
        key = (miovision_id,direction_name,movement_name,vehicle_name)
        self._studies_dir_mov_veh_id_mapping[key] = id
    
    def get_movement_vehicle_id(self, miovision_id: int, direction_name: str, movement_name : str, vehicle_name: str)->int:
        key = (miovision_id,direction_name,movement_name,vehicle_name)
        
        if key not in self._studies_dir_mov_veh_id_mapping:
            raise ValueError(f"Key {key} not found in movement_vehicles_mapping")
        
        return self._studies_dir_mov_veh_id_mapping[key]

    def get_all_vehicles(self)->list[str]:
        query_result = self._db_connection.select_existing_attributes(
            table_name=PredefinedTableNames.vehicles_types,
            query_attr=[PredefinedTableLabels.vehicles_types]
        )
        
        if len(query_result) == 0:
            raise RuntimeError("No Vehicles returned from get_all_vehicles() inside of TransactionContext")
        
        return [query[0] for query in query_result]
    
    def _get_query_result_for_id(self, table_name: str, lables: list[str], values: list[Any]):
        query_result = self._db_connection.select_existing_attributes(
            table_name=table_name,
            query_attr=['id'],
            where_labels=lables,
            where_values=values
        )
        if len(query_result) != 1:
            raise Exception(f"Non-singular result returned when querying ID column for {values}")
        
        return query_result[0][0]

    def get_direction_type_id(self, direction_name : str)->int:
        if direction_name not in self._direction_name_id_mapping:
            self._direction_name_id_mapping[direction_name] = self._get_query_result_for_id(
                table_name=PredefinedTableNames.direction_types.value,
                lables=[PredefinedTableLabels.direction_types.value],
                values=[direction_name]
            )
        return self._direction_name_id_mapping[direction_name]
    
    def get_movement_type_id(self, movement_name : str)->int:
        if movement_name not in self._movement_name_id_mapping:
            self._movement_name_id_mapping[movement_name] = self._get_query_result_for_id(
                table_name=PredefinedTableNames.movement_types.value,
                lables=[PredefinedTableLabels.movement_types],
                values=[movement_name]
            )
        return self._movement_name_id_mapping[movement_name]
    
    def get_vehicle_type_id(self, vehicle_name: str)->int:
        if vehicle_name not in self._vehicle_name_id_mapping:
            self._vehicle_name_id_mapping[vehicle_name] = self._get_query_result_for_id(
                table_name=PredefinedTableNames.vehicles_types,
                lables=[PredefinedTableLabels.vehicles_types],
                values=[vehicle_name]
            )
        return self._vehicle_name_id_mapping[vehicle_name]
    
    def update_direction_movement_id_mapping(self, miovision_id: int, direction_name: str, movement_name:str, id:int)->None:
        key = (miovision_id,direction_name,movement_name)
        self._studies_direction_movement_id_mapping[key] = id
    
    def get_direction_movement_id(self, miovision_id: int, direction_name : str, movement_name : str)->int:
        key = (miovision_id,direction_name,movement_name)
        if key not in self._studies_direction_movement_id_mapping:
            raise KeyError(f"Key {key} not found in direction_movement mapping")
        
        return self._studies_direction_movement_id_mapping[key]
    
    def update_path_movements_mapping(self, path: str, movement: str)->None:
        if path not in self._path_movements_mapping:
            self._path_movements_mapping[path] = set()
        self._path_movements_mapping[path].update([movement])
    
    def get_path_movements(self, path: str)->list[str]:
        if path not in self._path_movements_mapping:
            raise KeyError(f"Path {path} not found in path_movements mapping")
        
        return list(self._path_movements_mapping[path])
    
    def update_studies_directions_id_mapping(self,miovision_id:int, direction_name:str, id:int)->None:
        key = (miovision_id,direction_name)
        self._miovision_studies_directions_id_mapping[key] = id

    def get_study_direction_id(self, miovision_id:int, direction_name:str)->int:
        key = (miovision_id,direction_name)
        
        if key not in self._miovision_studies_directions_id_mapping:
            raise KeyError(f"Key {key} not found in studies_directions mapping")

        return self._miovision_studies_directions_id_mapping[key]
        
    def update_path_directions_mapping(self,path:str,direction:str)->None:
        if path not in self._path_directions_mapping:
            self._path_directions_mapping[path] = set()
        
        self._path_directions_mapping[path].update([direction])
        
    def get_path_directions(self, path:str)->list[str]:
        if path not in self._path_directions_mapping:
            raise KeyError(f"Provided path: {path} not in path directions mapping")
        
        return list(self._path_directions_mapping[path])

class CoreDataProvider(Protocol):
    def write_data(self)->None:...
    """
    Write data into database
    """

class CoreDataWriter:
    def __init__(self, core_providers:list[CoreDataProvider]) -> None:
        self._providers = core_providers
    
    def write_data(self)->None:
        for provider in self._providers:
            provider.write_data()

class StudiesDirectionsProvider:
    def __init__(self, base_validator: BaseFolderValidator, context: TransactionContext, database_connection : DatabaseUpdater, directions_extractor : DirectionsExtractor) -> None:
        self._paths = base_validator.get_files()
        self._context = context
        self._db_connection = database_connection
        self._extractor = directions_extractor
    
    def write_data(self)->None:
        print(f"Populating {PredefinedTableNames.studies_directions.value}")
        for path in tqdm.tqdm(self._paths):
            directions = self._extractor.extract_fields(path=path)
            for direction in directions:
                id = self._db_connection.update_db_and_return_id(
                    table_name=PredefinedTableNames.studies_directions.value,
                    labels=[
                        StudiesDirectionsTableColumns.direction_type_id.value,
                        StudiesDirectionsTableColumns.miovision_id.value
                    ],
                    values=[
                        self._context.get_direction_type_id(direction.direction_name),
                        direction.miovision_id
                    ]
                )

                self._context.update_studies_directions_id_mapping(direction.miovision_id,direction.direction_name,int(id))
                self._context.update_path_directions_mapping(str(path),direction.direction_name)

class DirectionsMovementsProvider:
    def __init__(self, base_validator: BaseFolderValidator, db_connection: DatabaseUpdater, extractor: MovementsExtractor, context: TransactionContext) -> None:
        self._paths = base_validator.get_files()
        self._db_connection = db_connection
        self._extractor = extractor
        self._context = context
    
    def write_data(self)->None:
        print(f"Populating {PredefinedTableNames.directions_movements.value}")
        for path in tqdm.tqdm(self._paths):
            extracted_data = self._extractor.extract_fields(
                path,
                self._context.get_path_directions(str(path))
            )
            
            for direction_movement in extracted_data:
                id = self._db_connection.update_db_and_return_id(
                    table_name=PredefinedTableNames.directions_movements.value,
                    labels=[
                        MovementsDirectionsTableColumns.movement_type_id.value,
                        MovementsDirectionsTableColumns.study_direction_id.value
                    ],
                    values=[
                        self._context.get_movement_type_id(direction_movement.movement_name),
                        self._context.get_study_direction_id(direction_movement.miovision_id,direction_movement.direction_name)
                    ]
                )
                
                self._context.update_direction_movement_id_mapping(miovision_id=direction_movement.miovision_id,
                                                                   direction_name=direction_movement.direction_name,
                                                                   movement_name=direction_movement.movement_name,
                                                                   id=int(id))
                
                self._context.update_path_movements_mapping(path=str(path),movement=direction_movement.movement_name)

class VehiclesAndGranularCountsProvider:
    def __init__(self, context: TransactionContext, db_connection: DatabaseUpdater, base_validator: BaseFolderValidator, extractor: GranularExtractor) -> None:
        self._paths = base_validator.get_files()
        self._context = context
        self._db_connection = db_connection
        self._extractor = extractor
    
    def write_data(self)->None:
        print(f"Populating {PredefinedTableNames.movements_vehicles.value} and {PredefinedTableNames.granular_count.value}.")
        for path in tqdm.tqdm(self._paths):
            vehicle_granular_counts = self._extractor.extract_fields(
                path=path,
                directions=self._context.get_path_directions(path=str(path)),
                movements=self._context.get_path_movements(path=str(path)),
                vehicles=self._context.get_all_vehicles()
            )
            
            for vehicle_granular_count in vehicle_granular_counts:
                try:
                    movement_vehicle_id = self._context.get_movement_vehicle_id(
                        miovision_id=vehicle_granular_count.miovision_id,
                        direction_name=vehicle_granular_count.direction_name,
                        movement_name=vehicle_granular_count.movement_name,
                        vehicle_name=vehicle_granular_count.vehicle_name
                    )
                except:
                    movement_vehicle_id = self._db_connection.update_db_and_return_id(
                        table_name=PredefinedTableNames.movements_vehicles.value,
                        labels=[
                            MovementVehiclesTableColumns.direction_movement_id.value,
                            MovementVehiclesTableColumns.vehicle_type_id.value
                        ],
                        values=[
                            self._context.get_direction_movement_id(miovision_id=vehicle_granular_count.miovision_id,
                                                                    direction_name=vehicle_granular_count.direction_name,
                                                                    movement_name=vehicle_granular_count.movement_name),
                            self._context.get_vehicle_type_id(vehicle_granular_count.vehicle_name)
                        ]
                    )
                    self._context.update_dir_mov_veh_id_mapping(miovision_id=vehicle_granular_count.miovision_id,
                                                                direction_name=vehicle_granular_count.direction_name,
                                                                movement_name=vehicle_granular_count.movement_name,
                                                                vehicle_name=vehicle_granular_count.vehicle_name,
                                                                id=int(movement_vehicle_id))
                    
                self._db_connection.update_db(
                        table_name=PredefinedTableNames.granular_count.value,
                        labels=[
                            GranularCountsTableColumns.movement_vehicle_id.value,
                            GranularCountsTableColumns.time_stamp.value,
                            GranularCountsTableColumns.traffic_count.value
                        ],
                        values=[
                            movement_vehicle_id,
                            vehicle_granular_count.time.time,
                            vehicle_granular_count.traffic_count
                        ]
                    )

class StudiesProvider:
    def __init__(self, base_validator: BaseFolderValidator, database_connection : DatabaseConnection, studies_extractor : StudiesExtractor) -> None:
        self._paths = base_validator.get_files()
        self._db_connection = database_connection
        self._studies_extractor = studies_extractor
    
    def write_data(self)->None:
        print(f"Populating {PredefinedTableNames.studies.value}")
        with self._db_connection as connection:
            for path in tqdm.tqdm(self._paths):
                study_fields = self._studies_extractor.extract_fields(path)
                connection.insert_new_information(
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
                        study_fields.study_date.date(),
                        study_fields.study_duration,
                        study_fields.study_type,
                        study_fields.study_name
                    ]
                )