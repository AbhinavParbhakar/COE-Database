import pandas as pd
from typing import Protocol
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class StudiesFields:
    miovision_id : int
    study_name : str
    study_duration : float
    study_type : str
    location_name : str
    latitude : float
    longitude : float
    project_name : str | None
    study_date : datetime

class MiovisionExtractor:
    @staticmethod
    def get_study_type(file_path:Path)->str:
        excel_name = file_path.stem
        study_type, miovision_id_string = excel_name.split('-')
        return study_type

    @staticmethod
    def get_miovision_id_string(file_path:Path)->str:
        excel_name = file_path.stem
        study_type, miovision_id_string = excel_name.split('-')
        return miovision_id_string

@dataclass
class StudiesDirectionsFields:
    miovision_id : int
    direction_name : str

@dataclass
class DirectionsMovementsFields:
    miovision_id : int
    direction_name : str
    movement_name : str
    
    
@dataclass
class GranularFields:
    miovision_id : int
    direction_name : str
    movement_name : str
    vehicle_name : str
    time : datetime
    traffic_count : int
    
class StudiesExtractor:
    def __init__(self) -> None:
        pass
    
    def extract_fields(self, path : Path) -> StudiesFields:
        # Get the summary and volume_df
        summary_df = pd.read_excel(path,sheet_name="Summary",header=None)
        
        try:
            # Let's start with populating the studies column first. 
            
            # Start with the Study_name
            labels_column = summary_df.columns[0]
            values_column = summary_df.columns[1]
            
            # Get the study type and miovision id
            study_type = MiovisionExtractor.get_study_type(path)
            miovision_id_string = MiovisionExtractor.get_miovision_id_string(path)
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
            project_name : str = summary_df[values_column][project_name_index].tolist()[0]
            start_time : datetime = summary_df[values_column][start_time_index].tolist()[0]
            end_time : datetime = summary_df[values_column][end_time_index].tolist()[0]
            location_name : str = summary_df[values_column][location_name_index].tolist()[0]
            lat_long_str : str = summary_df[values_column][lat_long_index].tolist()[0]
            
            # Get the values for study_date, study_duration (hrs), lat and long
            time_difference = end_time - start_time
            study_duration = time_difference.total_seconds() / 3600
            study_date = start_time
            latitude_str,longitude_str = lat_long_str.split(',')
            latitude = float(latitude_str)
            longitude = float(longitude_str)
            
            return StudiesFields(
                miovision_id=miovision_id,
                study_date=study_date,
                study_name=study_name,
                study_duration=study_duration,
                location_name=location_name,
                latitude=latitude,
                longitude=longitude,
                study_type=study_type,
                project_name = None if pd.isna(project_name) else project_name
            )
        except Exception as e:
            raise Exception(f'Error occurred when handling study {path}: {e}')
    
class DirectionsExtractor:
    def __init__(self) -> None:
        pass
    
    def extract_fields(self, path : Path) -> list[StudiesDirectionsFields]:
        direction_type_indicator = 'bound'
        direction_names : list[StudiesDirectionsFields] = []
        miovision_id_string = MiovisionExtractor.get_miovision_id_string(path)
        
        df = pd.read_excel(path,sheet_name=None)
        sheet_names = list(df.keys())
        
        for name in sheet_names:
            if direction_type_indicator in name:
                direction_names.append(StudiesDirectionsFields(
                    miovision_id=int(miovision_id_string),
                    direction_name=name
                ))
        
        return direction_names

class MovementsExtractor:
    def __init__(self) -> None:
        pass
    
    def _return_directions(self, path : Path) -> list[str]:
        direction_type_indicator = 'bound'
        direction_names = []
        
        df = pd.read_excel(path,sheet_name=None)
        sheet_names = list(df.keys())
        
        for name in sheet_names:
            if direction_type_indicator in name:
                direction_names.append(name)
        
        return direction_names
    
    def extract_fields(self, path : Path, directions: list[str]) -> list[DirectionsMovementsFields]:
        movements : list[DirectionsMovementsFields] = []
        directions_set = {direction for direction in directions}
        miovision_id_string = MiovisionExtractor.get_miovision_id_string(path)
        omit_names = ['Movement','Unnamed']
        direction_sheets = pd.read_excel(path,sheet_name=None,skiprows=1)
        
        for sheet_name, direction_df in direction_sheets.items():
            if sheet_name not in directions_set:
                continue
            
            for column in direction_df.columns:
                omit_flag = False
                for omit_name in omit_names:
                    if omit_name in column:
                        omit_flag = True
                
                if not omit_flag:
                    movements.append(DirectionsMovementsFields(
                        miovision_id=int(miovision_id_string),
                        direction_name=sheet_name,
                        movement_name=column
                    ))
        
        return movements
        
class GranularExtractor:
    def __init__(self) -> None:
        pass
    
    def extract_fields(self, path : Path, directions : list[str], movements : list[str], vehicles : list[str]) -> list[GranularFields]:
        directions_sets = {direction for direction in directions}
        movements_sets = {movement for movement in movements}
        vehicles_sets = {vehicle for vehicle in vehicles}
        miovision_id_string = MiovisionExtractor.get_miovision_id_string(path)
        granular_counts : list[GranularFields] = []
        direction_sheets = pd.read_excel(io=path,sheet_name=None,skiprows=1,index_col=0)
        vehicle_index = 0
        
        for sheet_name, directional_df in direction_sheets.items():
            if sheet_name not in directions_sets:
                continue
            
            direction_name = sheet_name
            movement_name = ''
            movement_row_labels = directional_df.columns
            
            for movement_row_label in movement_row_labels:
                if movement_row_label in movements_sets:
                    movement_name  = movement_row_label
                
                vehicle_class_name : str = directional_df[movement_row_label].iloc[vehicle_index]
                if vehicle_class_name not in vehicles_sets:
                    raise ValueError(f"{vehicle_class_name} not found in list of vehicles for path {path}.")
                
                granular_values : pd.Series[int] = directional_df[movement_row_label].iloc[vehicle_index + 1:].astype(int)
                
                for index, traffic_count in enumerate(granular_values):
                    if traffic_count == 0:
                        continue
                    time : datetime = granular_values.index[index]
                    if not isinstance(time, datetime):
                        # Offset of four rows in excel file for starting granular count
                        raise ValueError(f"Index not of type datetime for row {index + 4}, path: {path}")
                    
                    granular_counts.append(GranularFields(
                        miovision_id=int(miovision_id_string),
                        direction_name=direction_name,
                        movement_name=movement_name,
                        vehicle_name=vehicle_class_name,
                        time=time,
                        traffic_count=traffic_count
                    ))
                        
                        
        return granular_counts        