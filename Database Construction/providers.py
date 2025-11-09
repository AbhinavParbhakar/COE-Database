from pathlib import Path
import pandas as pd
from typing import Protocol, TypedDict, Self
import tqdm
from psycopg2 import connect, sql
from psycopg2.extras import RealDictCursor
from tables import Table


class BaseTypesProvider(Protocol):
    def return_information(self)->list[str]:...

class BaseTypeConfiguration(TypedDict):
    base_type_table_name:str
    base_type_label_name:str
    base_type_provider:BaseTypesProvider

class BaseFolderValidator:
    def __init__(self,base_folder_path:Path,validation_extension:str) -> None:
        if not base_folder_path.is_dir():
            raise Exception('Base Folder is not a directory')
        
        _files = [child for child in base_folder_path.iterdir()]
        
        for file in _files:
            if validation_extension != file.suffix:
                raise Exception(f'{file} does not contain the {validation_extension} extension.')
        
        self._files = _files
    
    def get_files(self)->list[Path]:
        return self._files

class DirectionsProvider:
    def __init__(self,base_folder:BaseFolderValidator) -> None:
        self.excel_files = base_folder.get_files()
        self.directions : set[str] | None = None
    
    def return_directions_per_file(self,path:Path)->list[str]:
        omit_sheets = ['Summary','Breakdown']
        direction_names = []
        
        df = pd.read_excel(path,sheet_name=None)
        sheet_names = list(df.keys())
        
        for name in sheet_names:
            omit_flag = False
            for ommited_name in omit_sheets:                
                if ommited_name in name:
                    omit_flag = True
                
            if not omit_flag:
                direction_names.append(name)
        
        return direction_names

    def get_directions(self)->list[str]:
        if self.directions is None:
            self.directions = set()
            for path in tqdm.tqdm(self.excel_files):
                file_directions = self.return_directions_per_file(path)
                self.directions.update(file_directions)
        
        return list(self.directions)

    def return_information(self)->list[str]:
        return self.get_directions()

class VehiclesProvider:
    def __init__(self,base_file:BaseFolderValidator,total_volume_breakdown_sheet:str) -> None:
        self.excel_files = base_file.get_files()
        self.total_volume_breakdown_sheet = total_volume_breakdown_sheet
        self.vehicles : set[str] | None = None
    
    def __return_vehicles_per_file(self,path:Path)->list[str]:
        try:
            df = pd.read_excel(path,sheet_name=self.total_volume_breakdown_sheet)
        except Exception as e:
            raise Exception(f'Error for file {path}: {e}')
        vehicles_column = df.columns[0]
        vehicles = []
        
        vehicles_start_label = 'Grand Total'
        vehicles_start_index = df[df[vehicles_column] == vehicles_start_label].index[0]
        vehicles_indices = df[df.index > vehicles_start_index].index
        vehicles_series : pd.Series[str] = df[vehicles_column][vehicles_indices]
        vehicles_list = vehicles_series.to_list()
        
        percentange_marker = '%'
        for vehicle in vehicles_list:
            if  percentange_marker not in vehicle:
                vehicles.append(vehicle)
        
        return vehicles
    
    def get_vehicles(self)->list[str]:
        if self.vehicles is None:
            self.vehicles = set()
            for file in tqdm.tqdm(self.excel_files):
                file_vehicles = self.__return_vehicles_per_file(file)
                self.vehicles.update(file_vehicles)
        
        return list(self.vehicles)
    
    def return_information(self)->list[str]:
        return self.get_vehicles()

class MovementsProvider:
    def __init__(self,base_folder:BaseFolderValidator,directions_provider:DirectionsProvider) -> None:
        self.excel_files = base_folder.get_files()
        self.directions_provider = directions_provider
        self.overall_movements : set[str] | None = None
        
        
    def __return_movements_per_file(self,path:Path)->list[str]:
        if self.overall_movements is None:
            directions_in_file = self.directions_provider.return_directions_per_file(path)
            self.overall_movements = set()
            direction_sheets = pd.read_excel(path,sheet_name=directions_in_file,skiprows=1)
            omit_names = ['Movement','Unnamed']
            
            for direction_df in direction_sheets.values():
                directional_movements = []
                for column in direction_df.columns:
                    omit_flag = False
                    for omit_name in omit_names:
                        if omit_name in column:
                            omit_flag = True
                    
                    if not omit_flag:
                        directional_movements.append(column)
                
                self.overall_movements.update(directional_movements)
        
        return list(self.overall_movements)

    def get_movements(self)->list[str]:
        self.movements : set[str] = set()
        
        for file in tqdm.tqdm(self.excel_files):
            file_movements = self.__return_movements_per_file(file)
            self.movements = self.movements.union(file_movements)
        
        return list(self.movements)
    
    def return_information(self)->list[str]:
        return list(self.movements)

class DatabaseConnection(Protocol):
    def __enter__(self)->Self:...
    
    def __exit__(self, exc_type: str, exc_val: Exception, exc_tb)->None:...
    
    def is_existing_table(self,table_name:str)->bool:...
    
    def insert_new_information(self,table_name:str,label_name:str,value_name:str)->bool:...
    
    def create_table(self,query:sql.Composed)->bool:...
    
    def is_existing_attr_in_table(self, attr_name: str, attr_value: str, table_name: str)->bool:...
    

class PostgresDatabaseConnection:
    def __init__(self,connection_string:str) -> None:
        self.connection = connect(connection_string)
        self.cursor = self.connection.cursor()
        self.context_manager_used = False
    
    def __enter__(self):
        self.context_manager_used = True
        return self 
    
    def __exit__(self, exc_type: str, exc_val: Exception, exc_tb)->None:
        if not exc_type:
            self.context_manager_used = False
            self.commit()
        else:
            raise Exception(f'Error occured: {exc_val}')
        
    
    def insert_new_information(self,table_name:str,label_name:str,value_name:str)->bool:
        try:
            query = sql.SQL("INSERT INTO {0} ({1}) VALUES (%s)").format(
                sql.Identifier(table_name),
                sql.Identifier(label_name)
            )
            self.cursor.execute(query,(value_name))
            if not self.context_manager_used:
                print('[WARNING] ContextManager not used for DatabaseConnection. Changes may not be commited. \nCall commit() explicity to commit changes.')
            
            return True
        except Exception as e:
            print(f'Error occured when trying to insert into {table_name}: {e}')
            return False
    
    def commit(self)->None:
        self.connection.commit()
        return
    
    def is_existing_table(self,table_name:str)->bool:
        required_attribute = "table_name"
        existing_tables_names : set[str] = set()
        
        query = sql.SQL("""
                            SELECT {attribute} from information_schema.tables
                            WHERE table_schema = 'public';
                        """).format(attribute=sql.Identifier(required_attribute))
        
        self.cursor.execute(query)
        
        table_names = self.cursor.fetchall()
        
        if len(table_names) == 0:
            return False
        else:
            existing_tables_names.update([table_name[0] for table_name in table_names])
        
        return table_name in existing_tables_names
        
    
    def create_table(self,query:sql.Composed)->bool:
        try:
            self.cursor.execute(query)
            return True
        except Exception as e:
            print(f'Exception occured when: {e}')
            return False
    
    def is_existing_attr_in_table(self, attr_name: str, attr_value: str, table_name: str)->bool:
        """ Checks if the given attribute name and value pair exist in the given table.
        
        ### Arguments
        ``attr_name`` -- Column name to be checked
        
        ``attr_value`` -- Value to be searched against in the given column name
        
        ``table_name`` -- Name of the table to be checked
        
        ### External Effects
        None
        
        ### Returns
        ``True`` if the given key-value exists in the table
        
        ``False`` if key-value pair doesn't exist. 
        
        """
        if not self.is_existing_table(table_name):
            raise Exception(f'Table {table_name} does not exist.')
        
        query = sql.SQL("""SELECT {attr_name} FROM {table_name} WHERE {attr_name} = %s;""").format(
                attr_name=sql.Identifier(attr_name),
                table_name=sql.Identifier(table_name)
            )
        
        self.cursor.execute(query,(attr_value))
        
        results = self.cursor.fetchall()
        
        if len(results) > 0:
            return True
        else:
            return False

class DatabaseTableWriter:
    def __init__(self,database_connection:DatabaseConnection,tables:list[Table]) -> None:
        self.connection = database_connection
        self.tables = tables
    
    def create_tables(self)->None:
        with self.connection:
            for table in self.tables:
                is_success = True
                if not self.connection.is_existing_table(table.get_table_name()):
                    is_success = self.connection.create_table(table.get_initialization_query())
                
                if not is_success:
                    raise Exception(f'Table creation query failed for table {table.get_table_name()}')

class DatabaseTypesWriter:
    def __init__(self,database_connection:DatabaseConnection,providers_info:list[BaseTypeConfiguration]) -> None:
        self.db_connection = database_connection
        self.providers_info = providers_info
        
    def write_into_tables(self)->None:
        with self.db_connection:
            for provider_info in self.providers_info:
                for value in provider_info['base_type_provider'].return_information():
                    is_success = True
                    if not self.db_connection.is_existing_attr_in_table(
                                attr_name=provider_info['base_type_label_name'],
                                attr_value=value,
                                table_name=provider_info['base_type_table_name']
                            ):
                                is_success = self.db_connection.insert_new_information(
                                    table_name = provider_info['base_type_table_name'],
                                    label_name = provider_info['base_type_label_name'],
                                    value_name = value
                                )
                    
                    if not is_success:
                        raise Exception(f'[Failure] value not sucessfully written into {provider_info['base_type_table_name']}\n for label: {provider_info['base_type_label_name']}')