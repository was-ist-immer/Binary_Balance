import sim_base as sim_g
import nowo1_base as nowo
import datetime as dt
import pandas as pd
import numpy as np
import nowo1_gui_base 

class logger(nowo.port_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        super().__init__(name, GUI, **kwargs)
        self.log_data: pd.DataFrame = pd.DataFrame()

    def clear_buffer(self):
        super().clear_buffer()
        self.log_data = pd.DataFrame()

    def ready_for_end(self):
        super().ready_for_end()
        self.log_data = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in self.buffer_data.items() ]))
        


# Nimmt nur den ersten Wert und bildet eine Tabelle
# wird verwendet bei gleichen sim_obj die nur einmal berechnet wurden
class log_sheet(nowo.port_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        self.log_data: pd.DataFrame = pd.DataFrame()
        super().__init__(name, GUI, **kwargs)
        self.sheet_colnames : list = []
        self.sheet_rownames : list = []
        self.sheet_data: pd.DataFrame = None
         
    
    def clear_buffer(self):
        super().clear_buffer()
        self.log_data = pd.DataFrame()


    def Init(self,  Values = [], Gui_For_Data  = None):
        #with self.info: print(self.name, 'init')
        super().Init(Values, Gui_For_Data)
        for name in self.buffer_data.keys():
            split_name = name.split('.', 1)
            if not split_name[0] in self.sheet_colnames:
                self.sheet_colnames.append(split_name[0])
            if not split_name[1] in self.sheet_rownames:    
                self.sheet_rownames.append(split_name[1])
        self.sheet_data = pd.DataFrame(columns = self.sheet_colnames, index = self.sheet_rownames)
        if self.Gui_For_Data:
            self.Gui_For_Data.Init_by_dataframe(self.sheet_data)


    def ready_for_end(self):
        super().ready_for_end()
        # self.log_data = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in self.buffer_data.items() ]))
        #with self.info: print(self.name, 'ready')
        for col_name in self.sheet_colnames:
            for row_name in self.sheet_rownames:
                key_name = col_name + '.' + row_name
                value = self.buffer_data[key_name]
                self.sheet_data.at[row_name, col_name] = value
        #self.sheet_data.to_clipboard()
        if self.Gui_For_Data:
            #with self.info: print(self.Gui_For_Data.name, 'ready_2')
            self.Gui_For_Data.ready_for_end()



class log_dataframe(nowo.port_base):
    def __init__(self, name: str, GUI : bool = False,  **kwargs):
        super().__init__(name, GUI, **kwargs)
        self.log_data: pd.DataFrame = pd.DataFrame()

    def clear_buffer(self):
        super().clear_buffer()
        self.log_data = pd.DataFrame()


    def ready_for_end(self):
        super().ready_for_end()
        new = pd.DataFrame()
        for name, valuelist in self.buffer_data.items():
            for value in valuelist:
                if isinstance(value, pd.DataFrame):
                    new = pd.concat([new,value], ignore_index=True)

        self.log_data = new
        self.col_name = self.log_data.columns.tolist()