from typing import Protocol, TypedDict
from psycopg2.sql import SQL, Identifier, Composed
from enum import Enum

class Table(Protocol):
    def get_initialization_query(self)->Composed:...
    def get_table_name(self)->str:...

class PredefinedTableNames(str, Enum):
    studies = 'studies'
    studies_directions = 'studies_directions'
    directions_movements = 'direction_movements'
    movements_vehicles = 'movements_vehicles'
    granular_count = 'granular_count'
    vehicles_types = 'vehicles_types'
    movement_types = 'movement_types'
    direction_types = 'direction_types'
    
class PredefinedTableLabels(str, Enum):
    vehicles_types = ""
    movement_types = ""
    direction_types = ""

class StudiesTable:
    def __init__(self,PredefinedTableNames) -> None:
        self.table_name = names.studies.value
        names.
        self.query = SQL("""
                   CREATE TABLE {table_name}(
                       miovision_id INTEGER,
                       study_name VARCHAR(100) NOT NULL,
                       study_duration DECIMAL NOT NULL,
                       study_type VARCHAR(100) NOT NULL,
                       location_name VARCHAR(100) NOT NULL,
                       latitude DECIMAL NOT NULL,
                       longitude DECIMAL NOT NULL,
                       project_name VARCHAR(100),
                       study_date DATE NOT NULL,
                       PRIMARY KEY(miovision_id)
                   );
                   """).format(table_name=Identifier(self.table_name))
    
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query

class StudiesDirectionsTable:
    def __init__(self,names:PredefinedTableNames) -> None:
        self.table_name = names.
        self.query = SQL("""CREATE TABLE {table_name}(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       miovision_id INTEGER,
                       direction_type_id INTEGER,
                       PRIMARY KEY(id),
                       CONSTRAINT fk_studies
                       FOREIGN KEY(miovision_id)
                       REFERENCES {studies_table}(miovision_id),
                       CONSTRAINT fk_direction_types
                       FOREIGN KEY(direction_type_id)
                       REFERENCES {direction_types}(id)
                   );
                   """).format(
                       table_name=Identifier(self.table_name),
                       studies_table=Identifier(names.studies),
                       direction_types=Identifier(names.direction_types)
                   )
    
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query

class DirectionsTypesTable:
    def __init__(self,names:PredefinedTableNames, labels:PredefinedTableLabels) -> None:
        self.table_name = names.direction_types
        self.query = SQL("""
            CREATE TABLE {direction_types}(
            id INTEGER GENERATED ALWAYS AS IDENTITY,
            {direction_name} VARCHAR(20) NOT NULL,
            PRIMARY KEY(id)
        );
        """).format(
            direction_types=Identifier(self.table_name),
            direction_name=Identifier(labels.)
        )
    
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query

class MovementTypesTable:
    def __init__(self,names:TableNames) -> None:
        self.table_name = names['movement_types']
        self.query = SQL("""
                   CREATE TABLE {movement_types}(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       movement_name VARCHAR(10) NOT NULL,
                       PRIMARY KEY(id)
                   );
        """).format(
            movement_types=Identifier(self.table_name)
        )
    
    def get_table_name(self)->str:
        return self.table_name

    def get_initialization_query(self)->Composed:
        return self.query

class VehicleTypesTable:
    def __init__(self,names:TableNames) -> None:
        self.table_name = names['vehicle_types']
        self.query = SQL("""
                       CREATE TABLE {vehicle_types}(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       vehicle_type_name VARCHAR(100) NOT NULL,
                       PRIMARY KEY(id)
                    );
        """).format(
            vehicle_types=Identifier(self.table_name)
        )
    
    def get_table_name(self)->str:
        return self.table_name

    def get_initialization_query(self)->Composed:
        return self.query

class DirectionsMovementsTable:
    def __init__(self,names:TableNames) -> None:
        self.table_name = names['directions_movements']
        self.query = SQL("""
                       CREATE TABLE {directions_movements}(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       study_direction_id INTEGER,
                       movement_type_id INTEGER,
                       PRIMARY KEY(id),
                       CONSTRAINT fk_studies_directions
                       FOREIGN KEY(study_direction_id)
                       REFERENCES {studies_directions}(id),
                       CONSTRAINT fk_movement_type
                       FOREIGN KEY(movement_type_id)
                       REFERENCES {movement_types}(id)
                   );
        """).format(
            directions_movements=Identifier(names['directions_movements']),
            studies_directions=Identifier(names['studies_directions']),
            movement_types=Identifier(names['movement_types'])
        )
    
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query

class MovementVehiclesTable:
    def __init__(self, names:TableNames) -> None:
        self.table_name = names['movements_vehicles']
        self.query = SQL("""
                       CREATE TABLE {movement_vehicle_classes}(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       direction_movement_id INTEGER,
                       vehicle_type_id INTEGER,
                       PRIMARY KEY(id),
                       CONSTRAINT fk_direction_movement
                       FOREIGN KEY(direction_movement_id)
                       REFERENCES {directions_movements}(id),
                       CONSTRAINT fk_vehicle_types
                       FOREIGN KEY(vehicle_type_id)
                       REFERENCES {vehicle_types}(id)
                   );
        """).format(
            movement_vehicle_classes=Identifier(self.table_name),
            directions_movements=Identifier(names['directions_movements']),
            vehicle_types=Identifier(names['vehicle_types'])
        )
        
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query

class GranularCountTable:
    def __init__(self, names:TableNames) -> None:
        self.table_name = names['granular_count']
        self.query = SQL("""
            CREATE TABLE {granular_count}(
                id INTEGER GENERATED ALWAYS AS IDENTITY,
                movement_vehicle_id INTEGER,
                time_stamp TIME NOT NULL,
                PRIMARY KEY(id),
                CONSTRAINT fk_movement_vehicle
                FOREIGN KEY(movement_vehicle_id)
                REFERENCES {movement_vehicle_classes}(id)
            );
        """).format(granular_count=Identifier(self.table_name), movement_vehicle_classes=Identifier(names['movements_vehicles']))
        
    def get_table_name(self)->str:
        return self.table_name
    
    def get_initialization_query(self)->Composed:
        return self.query