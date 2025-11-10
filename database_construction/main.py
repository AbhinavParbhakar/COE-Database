import providers.tables_providers as tables
from providers.types_providers import MovementsProvider, VehiclesProvider, DirectionsProvider, BaseTypesProvider, BaseFolderValidator, BaseTypeConfiguration
from providers.database_providers import PostgresDatabaseConnection, DatabaseTableWriter, DatabaseTypesWriter
from pathlib import Path
from dataclasses import dataclass
import dotenv
import os


def get_connection_string(connection_string:str)->str:
    dotenv.load_dotenv()
    try:
        connection_string =  os.environ[connection_string]
        return connection_string
    except KeyError as e:
        raise e

@dataclass
class ApplicationConfiguration:
    db_connection_string : str
    miovision_base_folder_name : str
    vehicle_class_total_volume_sheet_name : str
    validation_extension : str
    intitialize_setup : bool
    

class App:
    """Orchestration class that abstracts the flow of the database construction."""
    def __init__(self, app_configuration: ApplicationConfiguration) -> None:
        self._database_connection = PostgresDatabaseConnection(connection_string=app_configuration.db_connection_string)
        
        self.app_configuration = app_configuration
        
        self._initial_tables = self._return_initial_tables()
    

    def _initialize_database(self)->None:
        """Create a ``DatabaseTableWriter`` object, assigns it to ``self`` and run the initialization methods.
        
        ### Arguments
        No outside arguments

        ### External Effects
        Tables are populated in the database referenced via the database connection string
        
        ### Returns
        ``None``
        """
        self.database_writer = DatabaseTableWriter(
                                database_connection=self._database_connection,
                                tables=self._initial_tables
                                )
        
        self.database_writer.create_tables()
        
        return
    
    def _intialize_providers(self, base_validator: BaseFolderValidator)->None:
        """Creates a list of ``BaseTypesProvider`` objects and uses ``DatabaseTypesWriter`` to write these
        objects into the database. Assigns the database types writer to ``self``.
        
        ### Arguments
        ``base_validator`` -- Used to create ``BaseTypesProvider`` objects by validating the base folder path
        
        ### External Effects
        Populates the Base Types tables in the database with information.
        
        ### Returns
        ``None``
        
        """
        directions : BaseTypesProvider = DirectionsProvider(base_validator)
        
        movements : BaseTypesProvider = MovementsProvider(base_validator,directions)
        
        vehicles : BaseTypesProvider = VehiclesProvider(base_validator,self.app_configuration.vehicle_class_total_volume_sheet_name)
        
        directions_configuration = BaseTypeConfiguration(
                                    base_type_label_name=tables.PredefinedTableLabels.direction_types.value,
                                    base_type_table_name=tables.PredefinedTableNames.direction_types.value,
                                    base_type_provider=directions
                                    )
        
        movements_configuration = BaseTypeConfiguration(
                                    base_type_label_name=tables.PredefinedTableLabels.movement_types.value,
                                    base_type_table_name=tables.PredefinedTableNames.movement_types.value,
                                    base_type_provider=movements
                                    )
        
        vehicles_configuration = BaseTypeConfiguration(
                                    base_type_label_name=tables.PredefinedTableLabels.vehicles_types.value,
                                    base_type_table_name=tables.PredefinedTableNames.vehicles_types.value,
                                    base_type_provider=vehicles
                                    )
        
        base_configs = [
            directions_configuration,
            movements_configuration,
            vehicles_configuration
        ]
        
        self.base_types_writer = DatabaseTypesWriter(
                                database_connection=self._database_connection,
                                providers_info=base_configs
                            )
        
        self.base_types_writer.write_into_tables()
        
        return
        
        
    
    def _return_initial_tables(self)->list[tables.Table]:
        return [
            # Types tables intitialized first
            tables.MovementTypesTable(),
            tables.VehicleTypesTable(),
            tables.DirectionsTypesTable(),
            
            # Main Tables initialized in hierarchical order
            tables.StudiesTable(),
            tables.StudiesDirectionsTable(),
            tables.DirectionsMovementsTable(),
            tables.MovementVehiclesTable(),
            tables.GranularCountTable()
        ]
        
    
    def run(self)->None:
        """Runs the main flow of the application
        
        ### Arguments
        No oustide arguments
        
        ### External Effects
        Creates and populates tables in the database referenced by the database connection string. 
        
        ### Returns
        ``None``
        
        """
        if self.app_configuration.intitialize_setup:
            self._initialize_database()
            self._intialize_providers(BaseFolderValidator(
                                        base_folder_path=Path(app_configuration.miovision_base_folder_name),
                                        validation_extension=app_configuration.validation_extension
                                    ))
        
    
if __name__ == "__main__":
    
    app_configuration = ApplicationConfiguration(
                            db_connection_string = get_connection_string('LOCAL_DATABASE_URL'),
                            miovision_base_folder_name = 'Granular Miovision Files',
                            vehicle_class_total_volume_sheet_name = 'Total Volume Class Breakdown',
                            validation_extension = '.xlsx',
                            intitialize_setup = True
                        )
    
    application = App(app_configuration=app_configuration)
    application.run()
