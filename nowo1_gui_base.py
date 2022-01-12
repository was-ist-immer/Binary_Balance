import sim_base as sim_g
import nowo1_base as nowo
import datetime as dt
import pandas as pd
import numpy as np

import ipywidgets as widgets
import ipysheet
from ipysheet import from_dataframe
from IPython.display import display



class gui_ipysheet(nowo.gui_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        super().__init__(name, GUI, **kwargs)
        self.sheet : ipysheet.sheet = None 
        self.sheet_colnames : list = []
        self.sheet_rownames : list = []
        self.sheet_data: pd.DataFrame = None  
        self.dataframe_out: pd.DataFrame = None 


    def Init_by_dataframe(self, dataframe):
        with self.info: print(self.name, 'Init_by')
        self.sheet_data = dataframe
        self.sheet_colnames = list(self.sheet_data.head())
        self.sheet_rownames = list(self.sheet_data.index.tolist())


    def ready_for_end(self):
        with self.info: print(self.name, 'ready_1')
        buffer = self.sheet_data.values.T.tolist()
        # self.sheet.cells = (ipysheet.Cell(
        #     column_end=0, column_start=1, row_end=1, row_start=1, type='text', value='Hello'), 
        #     ipysheet.Cell(column_end=0, column_start=0, row_end=0, row_start=0, type='text', value='Hello'))

        ipysheet.cell_range(buffer[0], column_start=1)
       # self.dataframe_out = ipysheet.to_dataframe(self.sheet)
        #self.sheet_data.to_clipboard()
               
    def _create_gui(self):
       # sheet = ipysheet.sheet(rows = len(self.sheet_rownames) + 1, columns= len(self.sheet_colnames) + 1) 
        self.sheet = ipysheet.sheet(rows = len(self.sheet_rownames),  
                columns= len(self.sheet_colnames) + 1, 
                column_headers = ['variable'] + self.sheet_colnames)
     
        cols_1 = ipysheet.column(0, self.sheet_rownames, row_start = 0)
       
        total_box = widgets.VBox([self.sheet])
        self._GUI_itemlist.update({'sheet' : self.sheet})
        super()._create_gui()# Attention! --must-- because the widget get a parent attr.
        return  total_box