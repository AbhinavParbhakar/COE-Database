from typing import Protocol, TypedDict
from .types_providers import BaseFolderValidator
from pathlib import Path
import pandas as pd
from .tables_providers import PredefinedTableLabels


class CoreDataProvider(Protocol):
    def return_data_pairs(self)->list[dict[str,str]]:...
    """
    Returns the values to be inputted per row of data via a dict in ``<col_name>:<value>`` format. 
    """

class StudiesProvider:
    def __init__(self, base_validator: BaseFolderValidator) -> None:
        self._paths = base_validator.get_files()
        self._data : list[dict[str,str]] | None = None
    
    def _get_data_per_row(self,file_path:Path)->dict[str,str]:
        """
        
        """
        row_data : dict[str,str] = {}
        
        df = pd.read_excel(file_path)
        
        return row_data
    
    def return_data_pairs(self)->list[dict[str,str]]:
        """
        Returns the values to be inputted per row of data via a dict in ``<col_name>:<value>`` format. 
        """
        if self._data is None:
            self._data = []
            for path in self._paths:
                self._data.append(self._get_data_per_row(path))
        return self._data