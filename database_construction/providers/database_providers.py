from typing import Protocol, Self, Any, TypeVar
from psycopg2 import connect, sql
from .tables_providers import Table
import datetime
from datetime import _Date
from .types_providers import BaseTypeConfiguration


class DatabaseConnection(Protocol):
    def __enter__(self)->Self:...
    
    def __exit__(self, exc_type: str, exc_val: Exception, exc_tb)->None:...

    def select_existing_attributes(self, table_name : str, query_attr : list[str], where_labels : list[str] | None = None, where_values : list[Any] | None = None)->list[tuple]:...
    
    def is_existing_table(self,table_name:str)->bool:...
    
    def insert_new_information(self,table_name:str,labels:list[str],values:list[Any])->bool:...
    
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
        
    
    def insert_new_information(self,table_name:str,labels:list[str],values:list[Any])->bool:
        try:
            query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(',').join(map(sql.Identifier, labels)),
                sql.SQL(',').join(sql.SQL('%s') for _ in values)
            )
            self.cursor.execute(query,values)
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
        
        self.cursor.execute(query,(attr_value,))
        
        results = self.cursor.fetchall()
        
        if len(results) > 0:
            return True
        else:
            return False
    
    def select_existing_attributes(self, table_name : str, query_attr : list[str],where_labels : list[str] | None = None, where_values : list[Any] | None = None)->list[tuple]:
        if where_labels is not None and where_values is not None:
            if len(where_labels) != len(where_values):
                raise Exception("len() of where_labels must equal that of where_values.")
            
            query = sql.SQL("SELECT {} FROM {} WHERE {}").format(
                sql.SQL(', ').join(map(sql.Identifier,query_attr)),
                sql.Identifier(table_name),
                sql.SQL(' AND ').join([
                    sql.SQL('{} = %s').format(sql.Identifier(label))  
                    for label in where_labels
                    ])
            )
            
            self.cursor.execute(query,where_values)
        else:
            query = sql.SQL("SELECT {} FROM {}").format(
                sql.SQL(', ').join(map(sql.Identifier,query_attr)),
                sql.Identifier(table_name)
            )
            
            self.cursor.execute(query,where_values)
            
        return self.cursor.fetchall()

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
                                    labels = [provider_info['base_type_label_name']],
                                    values = [value]
                                )
                    
                    if not is_success:
                        raise Exception(f'[Failure] value: {value} not sucessfully written into {provider_info['base_type_table_name']}\n for label: {provider_info['base_type_label_name']}')


class DatabaseUpdater:
    def __init__(self, db_connection: DatabaseConnection) -> None:
        self._db_connection = db_connection
    
    def update_db_and_return_id(self,table_name : str, labels : list[str], values : list[Any])->int|str:
        self._db_connection.insert_new_information(
            table_name=table_name,
            labels=labels,
            values=values
        )
        
        query_results = self._db_connection.select_existing_attributes(
            table_name=table_name,
            query_attr=['id'],
            where_labels=labels,
            where_values=values
        )
        
        if len(query_results) != 1:
            raise Exception(f'Non-singular result returned for ID when looking for {values}')
        
        return query_results[0][0]
    
    def update_db(self,table_name : str, labels : list[str], values : list[Any])->None:
        self._db_connection.insert_new_information(
            table_name=table_name,
            labels=labels,
            values=values
        )
        