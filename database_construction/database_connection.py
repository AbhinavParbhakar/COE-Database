import os
import psycopg2
from dotenv import load_dotenv
import pandas as pd
from gather_names import ColumnNames
import datetime
import tqdm

def create_dummy_table(connection_string:str)->None:
    """
    Create a dummy table called books in the database, and prints the results. 
    Used as a **sanity check** to ensure that connection to the hosted database is established.
    
    ### Parameters:
    1. connection_string : ``str`` 
        - The string passed into the psycopg2 modules to connection to the database.
    
    ### Returns 
    None
    
    ### Effects
    Creation of a database called **books** in the database. 
    """
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    
    cursor.execute("""
                   DROP TABLE IF EXISTS books;
                   """)
    
    cursor.execute("""
                   CREATE TABLE books(
                       id SERIAL PRIMARY KEY,
                       title VARCHAR(255) NOT NULL,
                       pages SMALLINT NOT NULL
                   );
                   """)
    
    cursor.execute("""
                   INSERT INTO books (title,pages)
                   VALUES
                   ('Harry Potter and the Chamber of Secrets',750),
                   ('The US Constitution',20000)
                   RETURNING id
                   ;
                   """)
    connection.commit()
    cursor.execute("""
                             SELECT *
                             FROM books;
                             """)
    
    results = cursor.fetchall()
    print(results)

def configure_schema(connection_string:str)->None:
    """
    Configure the database according to Schema Version 3
    
    ### Parameters:
    1. connection_string : ``str``
        - The connection string passed into psycopg2 to connect to the database.
    
    ### Returns:
    None
    
    ### Effects:
    Creates the inital configuration of the relations in the hosted database.
    """
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    
    relation_names = ['STUDIES','STUDIES_DIRECTIONS','DIRECTION_TYPES','DIRECTIONS_MOVEMENTS','movement_types','movement_vehicle_classes','vehicle_types']
    
    for relation in relation_names:
        cursor.execute(f"DROP TABLE IF EXISTS {relation} CASCADE;")
    
    connection.commit()
    
    cursor.execute("""
                   CREATE TABLE studies(
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
                   """)

    cursor.execute("""
                   CREATE TABLE direction_types(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       direction_name VARCHAR(20) NOT NULL,
                       PRIMARY KEY(id)
                   );
                   """)

    cursor.execute("""
                   CREATE TABLE movement_types(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       movement_name VARCHAR(10) NOT NULL,
                       PRIMARY KEY(id)
                   );
                   """)

    
    cursor.execute("""
                   CREATE TABLE vehicle_types(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       vehicle_type_name VARCHAR(100) NOT NULL,
                       PRIMARY KEY(id)
                    );
                   """)
    
    cursor.execute("""
                   CREATE TABLE studies_directions(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       miovision_id INTEGER,
                       direction_type_id INTEGER,
                       PRIMARY KEY(id),
                       CONSTRAINT fk_studies
                       FOREIGN KEY(miovision_id)
                       REFERENCES studies(miovision_id),
                       CONSTRAINT fk_direction_types
                       FOREIGN KEY(direction_type_id)
                       REFERENCES direction_types(id)
                   );
                   """)
    
    cursor.execute("""
                   CREATE TABLE directions_movements(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       study_direction_id INTEGER,
                       movement_type_id INTEGER,
                       PRIMARY KEY(id),
                       CONSTRAINT fk_studies_directions
                       FOREIGN KEY(study_direction_id)
                       REFERENCES studies_directions(id),
                       CONSTRAINT fk_movement_type
                       FOREIGN KEY(movement_type_id)
                       REFERENCES movement_types(id)
                   );
                   """)
    
    cursor.execute("""
                   CREATE TABLE movement_vehicle_classes(
                       id INTEGER GENERATED ALWAYS AS IDENTITY,
                       direction_movement_id INTEGER,
                       vehicle_type_id INTEGER,
                       vehicle_count INTEGER,
                       PRIMARY KEY(id),
                       CONSTRAINT fk_direction_movement
                       FOREIGN KEY(direction_movement_id)
                       REFERENCES directions_movements(id),
                       CONSTRAINT fk_vehicle_types
                       FOREIGN KEY(vehicle_type_id)
                       REFERENCES vehicle_types(id)
                   );
                   """)
    connection.commit()

def input_directions(connection_string:str)->None:
    """
    Populates the directions data from the provided Miovision datasets. 
    
    ### Parameters
    1. connection_string: ``str``
        - Used to connect to the database
    
    ### Returns
    None
    
    ### Effects
    Creation of tuples in the relations configured for Schema Version 2. 
    """
    connection = psycopg2.connect(connection_string)
    cursors = connection.cursor()
    
    directions = ['Northeastbound', 'Westbound', 'Eastbound', 'Southeastbound', 'Northbound', 'Northwestbound', 'Southbound', 'Southwestbound']
    
    for direction in directions:
        cursors.execute(f"""
                        INSERT INTO direction_types (direction_name)
                        VALUES ('{direction}');
                        """)
        
        connection.commit()
        
def input_vehicle_types(connection_string:str)->None:
    """
    Populates the vehicle class tables with the information on all possible types of vehicles. 
    
    ### Parameters
    1. connection_string: ``str``
        - Used to connect to the database
    
    ### Returns
    Nothing
    
    ### Effects
    Creates corrsponding tuples in the vehicle_types table in the database.
    """
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    
    vehicle_classes = ['Cars', 'Articulated Trucks and Single-Unit Trucks', 
                        'Buses', 'Pedestrians', 'Light Goods Vehicles', 'Heavy', 
                        'Bicycles on Road', 'Bicycles on Crosswalk', 'Motorcycles',
                        'Lights', 'Articulated Trucks', 'Buses and Single-Unit Trucks',
                        'Bicycles', 'Single-Unit Trucks', 'Lights and Motorcycles', 'Vehicles', 
                        'Trams and Road Trains', 'Heavy and Lights', 'E-Scooters', 'e-Scooters (Road)']
    
    for veh_class in vehicle_classes:
        cursor.execute(f"""
                        INSERT INTO vehicle_types (vehicle_type_name)
                        VALUES ('{veh_class}');
                        """)
    
    connection.commit()

def input_movement_types(connection_string:str)->None:
    """
    Input the various movement types in the movement_types table in the database.
    
    ### Parameters:
    1. connection_string: ``str``
        - The string used for connecting to the database.
    
    ### Returns
    Nothing
    
    ### Effects
    Creates the corresponding utples in the movement_types table in the database.
    """
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    
    movement_types = ['Peds', 'Right', 'Peds CW', 'Hard right',
                      'Peds CCW', 'Bear right', 'Bear left', 
                      'Hard left', 'U-Turn', 'Left', 'Thru']
    
    for mov_type in movement_types:
        cursor.execute(f"""
                       INSERT INTO movement_types (movement_name)
                       VALUES ('{mov_type}');
                       """)
    connection.commit()

def get_study_type_miovision_id_tuple(file_path:str)->tuple[str,str]:
    excel_name_with_file_extension = file_path.split('/')[-1]
    excel_name = excel_name_with_file_extension.split('.')[0]
    study_type, miovision_id_string = excel_name.split('-')
    return (study_type,miovision_id_string)

def input_studies_information(cursor,file_path:str)->int:
    """
    Add a tuple to the studies relation using the information provided in the excel file.
    
    ### Parameters
    1. cursor: An instance of the psycopg2 Cursor class
        - Used to insert data in the relation.
    2. file_path : ``str``
        - File path used to reference the DataFrame containing info.
        
    ### Returns
    The Miovision ID in the form of an integer.
    
    ### Effects
    Creates a tuple in the studies relation. 
    """ 
    # Get the summary and volume_df
    summary_df = pd.read_excel(file_path,sheet_name="Summary",header=None)
    
    # Let's start with populating the studies column first. 
    
    # Start with the Study_name
    labels_column = summary_df.columns[0]
    values_column = summary_df.columns[1]
    
    # Get the study type and miovision id
    study_type, miovision_id_string = get_study_type_miovision_id_tuple(file_path)
    miovision_id = int(miovision_id_string)
    
    # Get the relevant indices
    study_name_index = summary_df[labels_column] == "Study Name"
    project_name_index = summary_df[labels_column] == "Project"
    start_time_index = summary_df[labels_column] == "Start Time"
    end_time_index = summary_df[labels_column] == "End Time"
    location_name_index = summary_df[labels_column] == "Location"
    lat_long_index = summary_df[labels_column] == "Latitude and Longitude"
    
    # Get the values for each index
    study_name : str= summary_df[values_column][study_name_index].tolist()[0]
    project_name = summary_df[values_column][project_name_index].tolist()[0]
    start_time : datetime.datetime = summary_df[values_column][start_time_index].tolist()[0]
    end_time : datetime.datetime = summary_df[values_column][end_time_index].tolist()[0]
    location_name : str = summary_df[values_column][location_name_index].tolist()[0]
    lat_long_str : str = summary_df[values_column][lat_long_index].tolist()[0]
    
    # Get the values for study_date, study_duration (hrs), lat and long
    time_difference = end_time - start_time
    study_duration = time_difference.total_seconds() / 3600
    study_date = start_time.strftime("%Y-%m-%d")
    latitude_str,longitude_str = lat_long_str.split(',')
    latitude = float(latitude_str)
    longitude = float(longitude_str)
    
    # Clean location_name and study_name
    
    study_name = study_name.replace("'"," ")
    
    if not pd.isna(location_name):
        location_name = location_name.replace("'"," ")
    
    cursor.execute(f"""
                   INSERT INTO studies (
                       miovision_id,
                       study_name,
                       study_duration,
                       study_type,
                       location_name,
                       latitude,
                       longitude,
                       project_name,
                       study_date
                   )
                   VALUES (
                       {miovision_id},
                       '{study_name}',
                       {study_duration},
                       '{study_type}',
                       '{location_name}',
                       {latitude},
                       {longitude},
                       '{project_name}',
                       '{study_date}'
                   );
                   """)
    
    return miovision_id

def populate_studies_data(connection_string:str)->None:
    """
    Internally called the ColumnNames class to populate the studies, studies_directions, directions_movements, and
    movement_vehicle_classes tables for each study.
    
    ### Parameters:
    1. connection_string: ``str``
        - String used to connnec to the database
    
    ### Returns:
    Nothing
    
    ### Effects:
    Creates corresponding tuple in the studies, studies_directions, directions_movements, and
    movement_vehicle_classes tables in the database. 
    """
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    
    column_names = ColumnNames(start_year=2010,
                               end_year=2024,
                               compute_direction_types=False,
                               compute_movement_types=False,
                               compute_vehicle_types=False)
    files = column_names.get_file_names()
    
    print("Populating studies relation: ")
    for file_path in tqdm.tqdm(files):
        input_studies_information(cursor=cursor,file_path=file_path)
        connection.commit()

def parse_volume_by_vehicle(total_volume_df:pd.DataFrame,label_column_name:str,movement_col_index:int,vehicles_labels_row_index:int,vehicles_id_mapping:dict[str,int]):
    vehicle_classes_labels = total_volume_df.loc[vehicles_labels_row_index:total_volume_df.shape[0],label_column_name].tolist()
    vehicle_classes_volumes = total_volume_df.iloc[vehicles_labels_row_index:total_volume_df.shape[0],movement_col_index].tolist()
    
    assert vehicle_classes_labels.__len__() == vehicle_classes_volumes.__len__()
    
    vehicle_class_volume_mapping = {}
    
    for i in range(0,len(vehicle_classes_labels)):
        vehicle_class_name = vehicle_classes_labels[i]
        vehicle_class_volume = vehicle_classes_volumes[i]
        if vehicle_class_name in vehicles_id_mapping and not pd.isna(vehicle_class_volume):
            vehicle_class_volume_mapping[vehicle_class_name] = vehicle_class_volume
        
    
    return vehicle_class_volume_mapping

def input_volume(cursor,file_path:str):
    total_volume_df = pd.read_excel(file_path,sheet_name="Total Volume Class Breakdown",header=None)
    labels_column = total_volume_df.columns[0]
    study_type, miovision_id_string = get_study_type_miovision_id_tuple(file_path=file_path)
    miovision_id = int(miovision_id_string)
    
    # Grab index for the rows that contain the directions, movements, and the start point of the labels for vehicle classes
    directions_row_index = total_volume_df[total_volume_df[labels_column] == 'Direction'].index.tolist()[0]
    movements_row_index = total_volume_df[total_volume_df[labels_column] == 'Start Time'].index.tolist()[0]
    vehicle_labels_row_index = total_volume_df[total_volume_df[labels_column] == 'Grand Total'].index.tolist()[0]
    
    # Grab the allowable inputs and id for all direction_types, movement_types, and vehicle_class_types
    
    cursor.execute("""
                   SELECT direction_name, id FROM direction_types;
                   """)
    
    direction_types_tuples : list[tuple] = cursor.fetchall()
    
    direction_types_id_mapping = {direction_tuple[0] : direction_tuple[1] for direction_tuple in direction_types_tuples}
    
    cursor.execute("""
                   SELECT movement_name, id FROM movement_types;
                   """)
    
    movement_types_tuples : list[tuple] = cursor.fetchall()
    
    movement_types_id_mapping = {movement_tuple[0] : movement_tuple[1] for movement_tuple in movement_types_tuples}
    
    cursor.execute("""
                   SELECT vehicle_type_name, id FROM vehicle_types;
                   """)
    
    vehicle_types_tuples : list[tuple] = cursor.fetchall()
    
    vehicle_types_id_mapping = {vehicle_tuple[0] : vehicle_tuple[1] for vehicle_tuple in vehicle_types_tuples}
    
    # Set the last found direction and default movement name
    last_found_direction = ""
    default_movement_name = "Thru" # There are multiple variations within the excel file that represent the thru movement. By default, if a movement value
                                   # is not in the mapping and is not equal to "App Total", then it represents the Thru movement. 
    
    # Iterate thru each cell in the direction and movement rows and check for matches
    for col_index in range(1,total_volume_df.shape[1]):
        direction_value = total_volume_df.iloc[directions_row_index,col_index]
        movement_value = total_volume_df.iloc[movements_row_index,col_index]
        
        if movement_value not in movement_types_id_mapping and not movement_value.__contains__("Total"):
            movement_value = default_movement_name
        
        if direction_value in direction_types_id_mapping:
            last_found_direction = direction_value
            
            # Add direction for the study
            cursor.execute(f"""
                           INSERT INTO studies_directions (
                               miovision_id,
                               direction_type_id
                           )
                           VALUES (
                               {miovision_id},
                               {direction_types_id_mapping[last_found_direction]}
                           )
                           RETURNING id;
                           """)
            
            study_direction_id = cursor.fetchone()[0]
            
        if movement_value in movement_types_id_mapping and last_found_direction != "":
            movement_id = movement_types_id_mapping[movement_value]
            
            # Add the movment for the corresponding study_direction
            cursor.execute(f"""
                           INSERT INTO directions_movements (
                               study_direction_id,
                               movement_type_id
                           )
                           VALUES (
                               {study_direction_id},
                               {movement_id}
                           )
                           RETURNING id;
                           """)
            
            direction_movement_id = cursor.fetchone()[0]
            
            vehicles_volumes_mapping = parse_volume_by_vehicle(
                total_volume_df=total_volume_df,
                label_column_name=labels_column,
                movement_col_index=col_index,
                vehicles_labels_row_index= vehicle_labels_row_index,
                vehicles_id_mapping=vehicle_types_id_mapping
            )
            
            for name, volume in vehicles_volumes_mapping.items():
                cursor.execute(f"""
                               INSERT INTO movement_vehicle_classes (
                                   direction_movement_id,
                                   vehicle_type_id,
                                   vehicle_count
                               )
                               VALUES (
                                   {direction_movement_id},
                                   {vehicle_types_id_mapping[name]},
                                   {volume}
                               );
                               """)
    

def populate_volume_data(connection_string:str)->None:
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    
    file_information = ColumnNames(start_year=2010,
                               end_year=2024,
                               compute_direction_types=False,
                               compute_movement_types=False,
                               compute_vehicle_types=False)
    
    files = file_information.get_file_names()
    
    print("Populating volume data: ")
    for file_path in tqdm.tqdm(files):
        input_volume(cursor=cursor,file_path=file_path)
        connection.commit()    

if __name__ == "__main__":
    load_dotenv()
    database_connection_string = os.getenv("DATABASE_URL")
    configure_schema(connection_string=database_connection_string)
    input_directions(database_connection_string)
    input_vehicle_types(database_connection_string)
    input_movement_types(database_connection_string)
    populate_studies_data(database_connection_string)
    populate_volume_data(connection_string=database_connection_string)