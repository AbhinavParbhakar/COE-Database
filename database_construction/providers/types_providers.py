from typing import Protocol, TypedDict
from pathlib import Path
import pandas as pd
import tqdm

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
        direction_type_indicator = 'bound'
        direction_names = []
        
        df = pd.read_excel(path,sheet_name=None)
        sheet_names = list(df.keys())
        
        for name in sheet_names:
            if direction_type_indicator in name:
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
        self.movements : set[str] | None = None
        
    def __return_movements_per_file(self,path:Path)->list[str]:
        overall_directions = { direction for direction in self.directions_provider.return_information()}
        direction_sheets = pd.read_excel(path,sheet_name=None,skiprows=1)
        omit_names = ['Movement','Unnamed']
        overall_movements : set[str] = set()
        
        for sheet_name, direction_df in direction_sheets.items():
            if sheet_name not in overall_directions:
                continue
            
            directional_movements : list[str] = []
            for column in direction_df.columns:
                omit_flag = False
                for omit_name in omit_names:
                    if omit_name in column:
                        omit_flag = True
                
                if not omit_flag:
                    directional_movements.append(column)
            
            overall_movements.update(directional_movements)
        
        return list(overall_movements)

    def get_movements(self)->list[str]:
        if self.movements is None:
            self.movements = set()
            for file in tqdm.tqdm(self.excel_files):
                file_movements = self.__return_movements_per_file(file)
                self.movements.update(file_movements)
        
        return list(self.movements)
    
    def return_information(self)->list[str]:
        return self.get_movements()