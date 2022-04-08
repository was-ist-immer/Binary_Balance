import sim_base as sim_g
import nowo1_base as nowo
from nowo1_gui_elements import Download_Button_csv
import datetime as dt
import pandas as pd
import numpy as np
import ipywidgets as widgets
#import pyperclip

class logger(nowo.port_base):
    def __init__(self, name: str,  init_methode :  str = 'normal',  **kwargs):
        super().__init__(name, init_methode, **kwargs)
        self.log_data: pd.DataFrame = pd.DataFrame()

    def clear_buffer(self):
        super().clear_buffer()
        self.log_data = pd.DataFrame()

    def ready_for_end(self):
        super().ready_for_end()
        self.log_data = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in self.buffer_data.items() ]))
        



class log_sheet(nowo.port_base):
    def __init__(self, name: str,  init_methode :  str = 'normal',  **kwargs):
        self.log_data: pd.DataFrame = pd.DataFrame()
        super().__init__(name, init_methode, **kwargs)
       
        self.sheet_rownames : list = []
        self.sheet_data: pd.DataFrame = None
        self.full_data: pd.DataFrame = None
        self._download_class = Download_Button_csv('sheet_data.csv')
         
    
    def clear_buffer(self):
        super().clear_buffer()
        self.log_data = pd.DataFrame()


    def on_clear_clicked(self, args):  
        #with self.info: print('on_clear_clicked' , self._init_para) 
        self.sheet_data.drop(self.sheet_data.columns, axis = 1, inplace = True)
        self.full_data.drop(self.sheet_data.columns, axis = 1, inplace = True)


    
      # Später im Parent
    def _create_gui(self):
        clear_button = widgets.Button(description='Löschen')
        clear_label = widgets.Label(value='Löschen')  
        clear_button.on_click(self.on_clear_clicked)
        
        
        download_button = self._download_class.button
        download_label = widgets.Label(value='Download')  
       
        
        #self.total_box = widgets.VBox([clear_label, clear_button, download_label, download_button])
        self.total_box = widgets.VBox([clear_button, download_button])
        self._GUI_itemlist.update({
            'clear_button' : clear_button,
            'clear_label' : clear_label,
            'download_button' : download_button,
            'download_label' : download_label,
        })
      
        super()._create_gui()# Attention! --must-- because the widget get a parent attr.
        return
       
  

    def Init(self,  
        Values = [], 
        Gui_For_Data  = None):

        with self.info: print(self.name, 'Init Sheet')
        super().Init(
            Values = Values, 
            Gui_For_Data = Gui_For_Data,
            para_from_Init = locals())
        
        if isinstance(self.sheet_data, pd.DataFrame) : return
        for name in self.buffer_data.keys():
            split_name = name.split('.', 1)
          
            if not split_name[1] in self.sheet_rownames:    
                self.sheet_rownames.append(split_name[1])
        self.sheet_data = pd.DataFrame(index = self.sheet_rownames)
        self.full_data  = pd.DataFrame(index = self.sheet_rownames) 
        if self.Gui_For_Data:
            self.Gui_For_Data.Init_by_dataframe(self.sheet_data)
        


    def ready_for_end(self):
        super().ready_for_end()
        for name, value in self.buffer_data.items():
            split_name = name.split('.', 1)
            col_name = split_name[0]
            if not col_name in self.sheet_data.columns:
                self.sheet_data[col_name] = ''
                self.full_data[col_name] = ''
            #with self.info: 
             #    print(split_name[1], col_name, value)
            # TODO Hier wird immer das erste Ausgegeben das sollt variable sein
            self.sheet_data.at[split_name[1], col_name] = value[0]
            self.full_data.at[split_name[1], col_name] = value
        
        csv_text = self.sheet_data.to_csv(sep = ';', decimal = ',')
        self._download_class.set_button(csv_text)
        if self.Gui_For_Data:
            self.Gui_For_Data.ready_for_end()




class log_dataframe(nowo.port_base):
    def __init__(self, name: str,  init_methode :  str = 'normal',  **kwargs):
        super().__init__(name, init_methode, **kwargs)
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