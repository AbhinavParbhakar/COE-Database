import pandas as pd
from psycopg2 import connect
from psycopg2._psycopg import cursor
from psycopg2.sql import SQL, Identifier
from pathlib import Path
import tqdm
import os
from dotenv import load_dotenv
import pytest
from providers.tables_providers import PredefinedTableNames, GranularCountsTableColumns
from providers.tables_providers import MovementsDirectionsTableColumns, MovementVehiclesTableColumns
from providers.tables_providers import StudiesTableColumns, StudiesDirectionsTableColumns


@pytest.fixture(scope='module')
def test_database_connection_string()->str:
    load_dotenv()
    url_key = 'LOCAL_DATABASE_URL'
    assert url_key in os.environ, f"{url_key} not found in environment variables"
    database_connection_str = os.environ['LOCAL_DATABASE_URL']
    return database_connection_str
    
@pytest.fixture(scope='module')
def test_database_connection(test_database_connection_string):
    connection = connect(test_database_connection_string)
    cursor = connection.cursor()
    yield cursor
    connection.close()

def excel_files()->list[Path]:
    test_files_directory = Path('Granular Miovision Files')
    
    assert test_files_directory.exists(), f'Test directory {test_files_directory} does not exist'
    
    return [path for path in test_files_directory.iterdir()]
    
def get_total_value_from_excel(path:Path)->int:
    total_volume_sheet_name = 'Total Volume Class Breakdown'
    total_volume_row_label = 'Grand Total'
    df = pd.read_excel(path,sheet_name = total_volume_sheet_name)
    
    total_values_including_label_df = df[df[df.columns[0]] == total_volume_row_label]
    total_values_df = total_values_including_label_df[total_values_including_label_df.columns[1:]]
    total_values_transposed_df = total_values_df.T
    total_values_series : pd.Series[int] = total_values_transposed_df[total_values_transposed_df.columns[0]]
    
    # Last value of the series is double counted in the sum, so need to substract it
    traffic_count = total_values_series.sum() - (2 * total_values_series.iloc[-1]) 
    
    return traffic_count

def get_total_value_from_db(path:Path, transaction: cursor)->int:
    stem_str = path.stem
    miovision_id : int = int(stem_str.split('-')[-1])
    
    query = SQL("""
        SELECT SUM(g.{traffic_count})
        FROM {studies} s
        JOIN {studies_directions} sd ON s.{studies_miovision_id} = sd.{sd_miovision_id}
        JOIN {directions_movements} dm ON sd.id = dm.{study_direction_id}
        JOIN {movements_vehicles} mv ON dm.id = mv.{direction_movement_id}
        JOIN {granular_count} g ON mv.id = g.{movement_vehicle_id}
        WHERE s.{studies_miovision_id} = %s;
    """).format(
        traffic_count = Identifier(GranularCountsTableColumns.traffic_count.value),
        studies = Identifier(PredefinedTableNames.studies.value),
        studies_directions = Identifier(PredefinedTableNames.studies_directions.value),
        directions_movements = Identifier(PredefinedTableNames.directions_movements.value),
        movements_vehicles = Identifier(PredefinedTableNames.movements_vehicles.value),
        granular_count = Identifier(PredefinedTableNames.granular_count.value),
        studies_miovision_id = Identifier(StudiesTableColumns.miovision_id.value),
        sd_miovision_id = Identifier(StudiesDirectionsTableColumns.miovision_id.value),
        study_direction_id = Identifier(MovementsDirectionsTableColumns.study_direction_id.value),
        direction_movement_id = Identifier(MovementVehiclesTableColumns.direction_movement_id.value),
        movement_vehicle_id = Identifier(GranularCountsTableColumns.movement_vehicle_id.value)
    )
    
    transaction.execute(query, [miovision_id])
    
    result = transaction.fetchone()
    if result is None:
        raise Exception(f'None returned from DB for {stem_str}')
    else:
        traffic_count = int(result[0])
        return traffic_count
    
@pytest.mark.parametrize('path',excel_files())
def test_total_db_values(path:Path,test_database_connection):
    assert get_total_value_from_db(path,test_database_connection) == get_total_value_from_excel(path), f"Inequal values for {path}"