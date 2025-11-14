from typing import Protocol, TypedDict
from psycopg2.sql import SQL, Identifier, Composed
from enum import StrEnum, auto

class Table(Protocol):
    def get_initialization_query(self)->Composed:...
    def get_table_name(self)->str:...

class PredefinedTableNames(StrEnum):
    studies = auto()
    studies_directions = auto()
    directions_movements = auto()
    movements_vehicles = auto()
    granular_count = auto()
    vehicles_types = auto()
    movement_types = auto()
    direction_types = auto()
    
class PredefinedTableLabels(StrEnum):
    vehicles_types = "vehicle_type_name"
    movement_types = "movement_type_name"
    direction_types = "direction_type_name"

class StudiesTableColumns(StrEnum):
    miovision_id = auto()
    study_name = auto()
    study_duration = auto()
    study_type = auto()
    location_name = auto()
    latitude = auto()
    longitude = auto()
    project_name = auto()
    study_date = auto()

class StudiesDirectionsTableColumns(StrEnum):
    miovision_id = auto()
    direction_type_id = auto()

class MovementsDirectionsTableColumns(StrEnum):
    study_direction_id = auto()
    movement_type_id = auto()

class MovementVehiclesTableColumns(StrEnum):
    direction_movement_id = auto()
    vehicle_type_id = auto()
    
class GranularCountsTableColumns(StrEnum):
    movement_vehicle_id = auto()
    time_stamp = auto()
    traffic_count = auto()

class StudiesTable:
    def __init__(self) -> None:
        self.table_name = PredefinedTableNames.studies.value
        self.query = SQL("""
                   CREATE TABLE {table_name}(
                       {miovision_id} INTEGER,
                       {study_name} VARCHAR(100) NOT NULL,
                       {study_duration} DECIMAL NOT NULL,
                       {study_type} VARCHAR(100) NOT NULL,
                       {location_name} VARCHAR(100) NOT NULL,
                       {latitude} DECIMAL NOT NULL,
                       {longitude} DECIMAL NOT NULL,
                       {project_name} VARCHAR(100),
                       {study_date} DATE NOT NULL,
                       PRIMARY KEY({miovision_id})
                   );
                   """).format(
                        table_name=Identifier(self.table_name),
                        miovision_id=Identifier(StudiesTableColumns.miovision_id.value),
                        study_name=Identifier(StudiesTableColumns.study_name.value),
                        study_duration=Identifier(StudiesTableColumns.study_duration.value),
                        study_type=Identifier(StudiesTableColumns.study_type.value),
                        location_name=Identifier(StudiesTableColumns.location_name.value),
                        latitude=Identifier(StudiesTableColumns.latitude.value),
                        longitude=Identifier(StudiesTableColumns.longitude.value),
                        project_name=Identifier(StudiesTableColumns.project_name.value),
                        study_date=Identifier(StudiesTableColumns.study_date.value)
                       )
    
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query

class StudiesDirectionsTable:
    def __init__(self,) -> None:
        self.table_name = PredefinedTableNames.studies_directions.value
        self.query = SQL("""CREATE TABLE {table_name}(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       {miovision_id} INTEGER,
                       {direction_type_id} INTEGER,
                       PRIMARY KEY(id),
                       CONSTRAINT fk_studies
                       FOREIGN KEY({miovision_id})
                       REFERENCES {studies_table}({studies_miovision_id}),
                       CONSTRAINT fk_direction_types
                       FOREIGN KEY({direction_type_id})
                       REFERENCES {direction_types}(id)
                   );
                   """).format(
                       table_name=Identifier(self.table_name),
                       miovision_id=Identifier(StudiesDirectionsTableColumns.miovision_id.value),
                       direction_type_id=Identifier(StudiesDirectionsTableColumns.direction_type_id.value),
                       studies_table=Identifier(PredefinedTableNames.studies.value),
                       studies_miovision_id=Identifier(StudiesTableColumns.miovision_id.value),
                       direction_types=Identifier(PredefinedTableNames.direction_types.value)
                   )
    
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query

class DirectionsTypesTable:
    def __init__(self) -> None:
        self.table_name = PredefinedTableNames.direction_types.value
        self.query = SQL("""
            CREATE TABLE {direction_types}(
            id INTEGER GENERATED ALWAYS AS IDENTITY,
            {direction_name} VARCHAR(20) NOT NULL,
            PRIMARY KEY(id)
        );
        """).format(
            direction_types=Identifier(self.table_name),
            direction_name=Identifier(PredefinedTableLabels.direction_types.value)
        )
    
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query

class MovementTypesTable:
    def __init__(self,) -> None:
        self.table_name = PredefinedTableNames.movement_types.value
        self.query = SQL("""
                   CREATE TABLE {movement_types}(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       {movement_label} VARCHAR(40) NOT NULL,
                       PRIMARY KEY(id)
                   );
        """).format(
            movement_types=Identifier(self.table_name),
            movement_label=Identifier(PredefinedTableLabels.movement_types.value)
        )
    
    def get_table_name(self)->str:
        return self.table_name

    def get_initialization_query(self)->Composed:
        return self.query

class VehicleTypesTable:
    def __init__(self,) -> None:
        self.table_name = PredefinedTableNames.vehicles_types.value
        self.query = SQL("""
                       CREATE TABLE {vehicle_types}(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       {vehicle_label} VARCHAR(100) NOT NULL,
                       PRIMARY KEY(id)
                    );
        """).format(
            vehicle_types=Identifier(self.table_name),
            vehicle_label=Identifier(PredefinedTableLabels.vehicles_types.value)
        )
    
    def get_table_name(self)->str:
        return self.table_name

    def get_initialization_query(self)->Composed:
        return self.query

class DirectionsMovementsTable:
    def __init__(self,) -> None:
        self.table_name = PredefinedTableNames.directions_movements.value
        self.query = SQL("""
                       CREATE TABLE {directions_movements}(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       {study_direction_id} INTEGER,
                       {movement_type_id} INTEGER,
                       PRIMARY KEY(id),
                       CONSTRAINT fk_studies_directions
                       FOREIGN KEY({study_direction_id})
                       REFERENCES {studies_directions}(id),
                       CONSTRAINT fk_movement_type
                       FOREIGN KEY({movement_type_id})
                       REFERENCES {movement_types}(id)
                   );
        """).format(
            directions_movements=Identifier(self.table_name),
            study_direction_id=Identifier(MovementsDirectionsTableColumns.study_direction_id.value),
            movement_type_id=Identifier(MovementsDirectionsTableColumns.movement_type_id.value),
            studies_directions=Identifier(PredefinedTableNames.studies_directions.value),
            movement_types=Identifier(PredefinedTableNames.movement_types.value)
        )
    
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query

class MovementVehiclesTable:
    def __init__(self) -> None:
        self.table_name = PredefinedTableNames.movements_vehicles.value
        self.query = SQL("""
                       CREATE TABLE {movement_vehicle_classes}(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       {direction_movement_id} INTEGER,
                       {vehicle_type_id} INTEGER,
                       PRIMARY KEY(id),
                       CONSTRAINT fk_direction_movement
                       FOREIGN KEY({direction_movement_id})
                       REFERENCES {directions_movements}(id),
                       CONSTRAINT fk_vehicle_types
                       FOREIGN KEY({vehicle_type_id})
                       REFERENCES {vehicle_types}(id)
                   );
        """).format(
            movement_vehicle_classes=Identifier(self.table_name),
            direction_movement_id=Identifier(MovementVehiclesTableColumns.direction_movement_id.value),
            vehicle_type_id=Identifier(MovementVehiclesTableColumns.vehicle_type_id.value),
            directions_movements=Identifier(PredefinedTableNames.directions_movements.value),
            vehicle_types=Identifier(PredefinedTableNames.vehicles_types.value)
        )
        
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query

class GranularCountTable:
    def __init__(self) -> None:
        self.table_name = PredefinedTableNames.granular_count.value
        self.query = SQL("""
            CREATE TABLE {granular_count}(
                id INTEGER GENERATED ALWAYS AS IDENTITY,
                {movement_vehicle_id} INTEGER,
                {time_stamp} TIME NOT NULL,
                {traffic_count} INTEGER NOT NULL,
                PRIMARY KEY(id),
                CONSTRAINT fk_movement_vehicle
                FOREIGN KEY({movement_vehicle_id})
                REFERENCES {movement_vehicle_classes}(id)
            );
        """).format(
            granular_count=Identifier(self.table_name),
            movement_vehicle_id=Identifier(GranularCountsTableColumns.movement_vehicle_id.value),
            time_stamp=Identifier(GranularCountsTableColumns.time_stamp.value),
            traffic_count=Identifier(GranularCountsTableColumns.traffic_count.value),
            movement_vehicle_classes=Identifier(PredefinedTableNames.movements_vehicles.value)
        )
        
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query