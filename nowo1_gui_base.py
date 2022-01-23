import sim_base as sim_g
import nowo1_base as nowo
import datetime as dt
import pandas as pd
import numpy as np

import ipywidgets as widgets
import ipysheet
from ipysheet import from_dataframe
from IPython.display import display


#TODO Optionen:
# Möglichkeit der flexiblen Anzahl von Spalten, oder fix
# Safe Button für die Tabelle
class gui_ipysheet(nowo.gui_base):
    def __init__(self, name: str, init_methode :  str = 'normal',  **kwargs):
        super().__init__(name, init_methode, **kwargs)
        self.sheet : ipysheet.sheet = None 
        self.sheet_data: pd.DataFrame = None  
        self.dataframe_out: pd.DataFrame = None 


    def Init_by_dataframe(self, dataframe):
        #with self.info: print(self.name, 'Init_by')
        self.sheet_data = dataframe
       
        

    def ready_for_end(self):
        col_names = ['Größen'] + list(self.sheet_data.columns)
        self.sheet.columns = len(col_names)
        rows_1 = ipysheet.row(0, col_names)
        buffer = self.sheet_data.values.tolist()
        value_field = []
        ipysheet.cell_range(buffer, column_start=1, row_start = 1)
      
                
    def _create_gui(self):
        first_col = list(self.sheet_data.index.values)
        self.sheet = ipysheet.sheet(rows = len(first_col) + 1, columns=1)
        cols_1 = ipysheet.column(0, first_col, row_start = 1, read_only=True)
        self.total_box = widgets.VBox([self.sheet])
        self._GUI_itemlist.update({'sheet' : self.sheet})
        super()._create_gui()# Attention! --must-- because the widget get a parent attr.
      
