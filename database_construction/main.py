import providers.tables_providers as tables
from providers.types_providers import MovementsProvider, VehiclesProvider, DirectionsProvider, BaseTypesProvider, BaseFolderValidator, BaseTypeConfiguration
from providers.database_providers import PostgresDatabaseConnection, DatabaseTableWriter, DatabaseTypesWriter, DatabaseUpdater
from pathlib import Path
from providers.core_providers import CoreDataProvider, StudiesDirectionsProvider, StudiesProvider, DirectionsMovementsProvider, VehiclesAndGranularCountsProvider
from providers.core_providers import TransactionContext, CoreDataWriter
from providers.extraction_providers import StudiesExtractor, DirectionsExtractor, MovementsExtractor, GranularExtractor
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
        
        self._db_updater = DatabaseUpdater(self._database_connection)
        
        self._base_validator = BaseFolderValidator(base_folder_path=Path(app_configuration.miovision_base_folder_name),
                                                   validation_extension=app_configuration.validation_extension)
        
        self._context = self._return_transaction_context()
    

    def _return_transaction_context(self)->TransactionContext:
        """
        Create and return a transaction context used to manage state between core providers
        
        ### Arguments
        None
        
        ### External Effects
        None
        
        ### Returns
        ``TransactionContext`` -- Context to be shared by core providers
        """
        return TransactionContext(
            db_connection=self._database_connection
        )

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
    
    def _return_core_providers(self,)->list[CoreDataProvider]:
        """
        Initialize and return list of core data providers, to be run in order of list
        
        ### Arguments
        ``base_validator`` -- Passed onto core providers
        
        ### External Effects
        None
        
        ### Returns
        ``list[CoreDataProvider]`` -- list of core providers
        """
        
        # Initialized in the order of running
        return [
            StudiesProvider(
                base_validator=self._base_validator,
                database_connection=self._database_connection,
                studies_extractor=StudiesExtractor()
            ),
            StudiesDirectionsProvider(
                base_validator=self._base_validator,
                context=self._context,
                database_connection=self._db_updater,
                directions_extractor=DirectionsExtractor()
            ),
            DirectionsMovementsProvider(
                base_validator=self._base_validator,
                db_connection=self._db_updater,
                extractor=MovementsExtractor(),
                context=self._context
            ),
            VehiclesAndGranularCountsProvider(
                context=self._context,
                db_connection=self._db_updater,
                base_validator=self._base_validator,
                extractor=GranularExtractor()
            )
        ]
    
    def _intitialize_base_providers(self, base_validator: BaseFolderValidator)->None:
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
    
    def _populate_core_tables(self, core_providers: list[CoreDataProvider])->None:
        """
        Creates a ``CoreDataWriter`` and uses it to populate core tables in the DB.
        
        ### Arguments
        ``core_providers`` - List of providers supplied to data writer
        
        ### External Effects
        Populates database of the linked connection
        
        ### Returns
        ``None``
        """
        writer = CoreDataWriter(core_providers)
        
        writer.write_data()
    
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
            self._intitialize_base_providers(self._base_validator)
        
        core_providers = self._return_core_providers()
        self._populate_core_tables(core_providers)
        
    
if __name__ == "__main__":
    
    app_configuration = ApplicationConfiguration(
                            db_connection_string = get_connection_string('LOCAL_DATABASE_URL'),
                            miovision_base_folder_name = 'Granular Miovision Files',
                            vehicle_class_total_volume_sheet_name = 'Total Volume Class Breakdown',
                            validation_extension = '.xlsx',
                            intitialize_setup = False
                        )
    
    application = App(app_configuration=app_configuration)
    application.run()
